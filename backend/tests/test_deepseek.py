"""
test_deepseek.py — Changement de fournisseur de modèle (demande explicite
de l'utilisateur) : les étapes lourdes (agent principal, vérificateur,
critique, validation finale, stratégie combative, et les fonctions de
rédaction/extraction substantielles) appellent désormais DeepSeek plutôt
que Claude, via analyse._appeler_modele_lourd / _appeler_modele_lourd_stream
(voir analyse.py, juste après _client()). MODEL_LEGER (garde-fou, détection
d'intention, notions juridiques) reste sur Claude, inchangé -- voir
test_analyse_moyens.py.

Portée : la mécanique d'appel (endpoint, en-têtes, corps de requête, parsing
de la réponse et du flux SSE) est testée directement, sans réseau réel
(requests.post mocké) -- le jugement réel du modèle DeepSeek n'est pas
testé ici, comme pour tout autre agent LLM de ce projet (voir
test_quality_pipeline.py, test_posture_dossier.py)."""

import analyse as legacy_analyse
import pytest


class _ReponseFactice:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


# --- _cle_api_deepseek -------------------------------------------------------

def test_cle_api_deepseek_lit_la_variable_denvironnement(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-depuis-env")
    assert legacy_analyse._cle_api_deepseek() == "sk-depuis-env"


def test_cle_api_deepseek_leve_une_erreur_claire_si_absente(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(legacy_analyse, "DEEPSEEK_KEY_FILE", legacy_analyse.paths.base_dir() / "fichier_deepseek_qui_nexiste_pas.txt")
    with pytest.raises(EnvironmentError, match="DeepSeek"):
        legacy_analyse._cle_api_deepseek()


# --- _appeler_modele_lourd (non-streaming) ----------------------------------

def test_appeler_modele_lourd_poste_au_bon_endpoint_avec_la_cle(monkeypatch):
    captures = {}

    def _post_factice(url, headers=None, json=None, timeout=None, **kwargs):
        captures["url"] = url
        captures["headers"] = headers
        captures["json"] = json
        captures["timeout"] = timeout
        return _ReponseFactice({"choices": [{"message": {"content": "  réponse du modèle  "}}]})

    monkeypatch.setattr(legacy_analyse.requests, "post", _post_factice)
    monkeypatch.setattr(legacy_analyse, "_cle_api_deepseek", lambda: "sk-deepseek-test")

    texte = legacy_analyse._appeler_modele_lourd("system prompt", [{"role": "user", "content": "bonjour"}], 500)

    assert texte == "réponse du modèle"  # .strip() appliqué
    assert captures["url"] == legacy_analyse.DEEPSEEK_API_URL
    assert captures["headers"]["Authorization"] == "Bearer sk-deepseek-test"
    assert captures["json"]["model"] == legacy_analyse.MODEL_LOURD
    assert captures["json"]["max_tokens"] == 500
    assert captures["json"]["messages"][0] == {"role": "system", "content": "system prompt"}
    assert captures["json"]["messages"][1] == {"role": "user", "content": "bonjour"}
    assert captures["timeout"] == 90


def test_appeler_modele_lourd_conserve_lhistorique_multi_tours(monkeypatch):
    """repondre_conversation transmet l'historique complet -- vérifie que
    _appeler_modele_lourd le retransmet tel quel, après le system prompt."""
    captures = {}
    historique = [
        {"role": "user", "content": "Première question"},
        {"role": "assistant", "content": "Première réponse"},
        {"role": "user", "content": "Deuxième question"},
    ]

    def _post_factice(url, headers=None, json=None, timeout=None, **kwargs):
        captures["json"] = json
        return _ReponseFactice({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(legacy_analyse.requests, "post", _post_factice)
    monkeypatch.setattr(legacy_analyse, "_cle_api_deepseek", lambda: "sk-deepseek-test")

    legacy_analyse._appeler_modele_lourd("system", historique, 800)

    assert captures["json"]["messages"] == [{"role": "system", "content": "system"}, *historique]


def test_appeler_modele_lourd_leve_si_le_statut_http_est_une_erreur(monkeypatch):
    def _post_factice(url, headers=None, json=None, timeout=None, **kwargs):
        return _ReponseFactice({"error": "invalid"}, status_code=401)

    monkeypatch.setattr(legacy_analyse.requests, "post", _post_factice)
    monkeypatch.setattr(legacy_analyse, "_cle_api_deepseek", lambda: "sk-invalide")

    with pytest.raises(RuntimeError):
        legacy_analyse._appeler_modele_lourd("system", [{"role": "user", "content": "x"}], 100)


# --- _appeler_modele_lourd_stream --------------------------------------------

class _ReponseStreamFactice:
    status_code = 200

    def __init__(self, trames):
        self._trames = trames

    def raise_for_status(self):
        pass

    def iter_lines(self, decode_unicode=True):
        return iter(self._trames)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_appeler_modele_lourd_stream_produit_les_fragments_dans_lordre(monkeypatch):
    trames = [
        'data: {"choices": [{"delta": {"content": "Bon"}}]}',
        "",  # ligne vide entre deux trames SSE -- doit être ignorée
        'data: {"choices": [{"delta": {"content": "jour"}}]}',
        'data: {"choices": [{"delta": {}}]}',  # trame sans contenu (ex. rôle initial) -- ignorée
        "data: [DONE]",
    ]
    captures = {}

    def _post_factice(url, headers=None, json=None, timeout=None, stream=None, **kwargs):
        captures["json"] = json
        captures["stream"] = stream
        return _ReponseStreamFactice(trames)

    monkeypatch.setattr(legacy_analyse.requests, "post", _post_factice)
    monkeypatch.setattr(legacy_analyse, "_cle_api_deepseek", lambda: "sk-deepseek-test")

    fragments = list(legacy_analyse._appeler_modele_lourd_stream("system", [{"role": "user", "content": "bonjour"}], 500))

    assert fragments == ["Bon", "jour"]
    assert captures["stream"] is True
    assert captures["json"]["stream"] is True


def test_appeler_modele_lourd_stream_sarrete_meme_sans_trame_done(monkeypatch):
    """Un flux qui se termine sans "data: [DONE]" (connexion coupée) ne
    doit jamais planter -- il s'arrête simplement à la fin des lignes
    disponibles."""
    trames = ['data: {"choices": [{"delta": {"content": "partiel"}}]}']

    def _post_factice(url, headers=None, json=None, timeout=None, stream=None, **kwargs):
        return _ReponseStreamFactice(trames)

    monkeypatch.setattr(legacy_analyse.requests, "post", _post_factice)
    monkeypatch.setattr(legacy_analyse, "_cle_api_deepseek", lambda: "sk-deepseek-test")

    fragments = list(legacy_analyse._appeler_modele_lourd_stream("system", [], 500))
    assert fragments == ["partiel"]


# --- Répartition des fonctions entre les deux fournisseurs -------------------

def test_les_agents_qualite_et_lagent_principal_utilisent_le_modele_lourd(monkeypatch):
    """Preuve que les fonctions concernées appellent bien
    _appeler_modele_lourd (DeepSeek) et non plus _client() (Claude)."""
    appels = []
    monkeypatch.setattr(legacy_analyse, "_appeler_modele_lourd", lambda *a, **k: appels.append(1) or '{"arguments": [], "points_attention": []}')
    legacy_analyse.analyser_conclusions("texte de conclusions")
    assert appels == [1]


class _ClientFactice:
    """Client Anthropic factice minimal -- garde-fou resté sur Claude, pas
    d'appel réseau réel dans ce test."""

    def __init__(self):
        self.messages = self

    def create(self, **kwargs):
        return type("R", (), {"content": [type("C", (), {"text": "{}"})()]})()


def test_le_garde_fou_et_la_detection_dintention_restent_sur_claude(monkeypatch):
    """Preuve inverse : ces fonctions n'appellent jamais _appeler_modele_lourd."""
    appels_lourd = []
    monkeypatch.setattr(legacy_analyse, "_appeler_modele_lourd", lambda *a, **k: appels_lourd.append(1) or "{}")
    monkeypatch.setattr(legacy_analyse, "_client", lambda: _ClientFactice())
    legacy_analyse.evaluer_garde_fou_entree("Un texte assez long pour dépasser le raccourci de vingt-cinq caractères.")
    assert appels_lourd == []


# --- Mode démo : les deux clés sont désormais nécessaires --------------------

def test_cle_api_deepseek_configuree_lit_la_variable_denvironnement(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-depuis-env")
    assert legacy_analyse.cle_api_deepseek_configuree() is True


def test_cle_api_deepseek_configuree_est_fausse_si_absente(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(legacy_analyse, "DEEPSEEK_KEY_FILE", legacy_analyse.paths.base_dir() / "fichier_deepseek_qui_nexiste_pas.txt")
    assert legacy_analyse.cle_api_deepseek_configuree() is False


def test_mode_demo_serveur_exige_les_deux_cles(monkeypatch):
    """Une seule des deux clés configurée (Anthropic sans DeepSeek, ou
    l'inverse) doit encore activer le mode démo -- sinon un visiteur
    atteindrait une erreur DeepSeek/Anthropic moins lisible qu'une 503 de
    mode démo (voir demo.mode_demo_serveur)."""
    from app import demo

    monkeypatch.setattr(demo, "DEMO_MODE_FORCE", False)

    monkeypatch.setattr(legacy_analyse, "cle_api_configuree", lambda: True)
    monkeypatch.setattr(legacy_analyse, "cle_api_deepseek_configuree", lambda: False)
    assert demo.mode_demo_serveur() is True

    monkeypatch.setattr(legacy_analyse, "cle_api_configuree", lambda: False)
    monkeypatch.setattr(legacy_analyse, "cle_api_deepseek_configuree", lambda: True)
    assert demo.mode_demo_serveur() is True

    monkeypatch.setattr(legacy_analyse, "cle_api_configuree", lambda: True)
    monkeypatch.setattr(legacy_analyse, "cle_api_deepseek_configuree", lambda: True)
    assert demo.mode_demo_serveur() is False
