"""
test_model_router.py — Chantier "optimisation des coûts API" : DeepSeek
(hébergé via NVIDIA NIM, voir analyse.py::NVIDIA_NIM_BASE_URL) comme second
fournisseur, réservé aux tâches d'extraction/résumé (analyse.TypeTache),
routé par analyse._appeler_modele. L'analyse d'arguments juridiques et la
génération de plaidoirie restent exclusivement sur Claude, sans exception --
voir test_verrouillage_claude_pour_analyse_et_generation ci-dessous.

Portée : mécanique du routage, du logging et du câblage garde-fou/citations
sur les deux endpoints concernés -- sans appel réseau réel, comme pour tout
autre agent LLM de ce projet (voir test_security_guard.py, test_deepseek.py
historique)."""

import analyse as legacy_analyse
import pytest
from app.security_guard import DemandeRefusee
from fastapi import HTTPException


# --- Fakes SDK OpenAI (fournisseur DeepSeek/NVIDIA) --------------------------

class _FakeUsageDeepseek:
    def __init__(self, prompt_tokens=10, completion_tokens=5):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _FakeChoice:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()


class _FakeReponseDeepseek:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]
        self.usage = _FakeUsageDeepseek()


class _FakeCompletions:
    def __init__(self, content):
        self._content = content
        self.captured = None

    def create(self, **kwargs):
        self.captured = kwargs
        return _FakeReponseDeepseek(self._content)


class _FakeClientDeepseek:
    def __init__(self, content="{}"):
        self.chat = type("Chat", (), {})()
        self.chat.completions = _FakeCompletions(content)


# --- Fakes SDK Anthropic (fournisseur Claude) --------------------------------

class _FakeUsageClaude:
    def __init__(self, input_tokens=20, output_tokens=8):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeReponseClaude:
    def __init__(self, content):
        self.content = [type("C", (), {"text": content})()]
        self.usage = _FakeUsageClaude()


class _FakeMessagesClaude:
    def __init__(self, content):
        self._content = content
        self.captured = None

    def create(self, **kwargs):
        self.captured = kwargs
        return _FakeReponseClaude(self._content)


class _FakeClientClaude:
    def __init__(self, content="{}"):
        self.messages = _FakeMessagesClaude(content)


# --- _cle_api_nvidia / cle_api_deepseek_configuree ---------------------------

def test_cle_api_nvidia_lit_la_variable_denvironnement(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    assert legacy_analyse._cle_api_nvidia() == "nvapi-test"


def test_cle_api_nvidia_leve_une_erreur_claire_si_absente(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(legacy_analyse, "NVIDIA_KEY_FILE", legacy_analyse.paths.base_dir() / "fichier_nvidia_qui_nexiste_pas.txt")
    with pytest.raises(EnvironmentError, match="NVIDIA"):
        legacy_analyse._cle_api_nvidia()


def test_cle_api_deepseek_configuree_reflete_la_cle_nvidia(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    assert legacy_analyse.cle_api_deepseek_configuree() is True
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(legacy_analyse, "NVIDIA_KEY_FILE", legacy_analyse.paths.base_dir() / "fichier_nvidia_qui_nexiste_pas.txt")
    assert legacy_analyse.cle_api_deepseek_configuree() is False


# --- Table de routage --------------------------------------------------------

def test_verrouillage_claude_pour_analyse_et_generation():
    """Sans exception : quoi qu'il arrive au reste de la table, ces deux
    tâches ne doivent jamais pointer vers autre chose que Claude."""
    assert legacy_analyse._TACHES_VERS_FOURNISSEUR[legacy_analyse.TypeTache.ANALYSE] == "claude"
    assert legacy_analyse._TACHES_VERS_FOURNISSEUR[legacy_analyse.TypeTache.GENERATION] == "claude"


def test_extraction_resume_et_indexation_vont_vers_deepseek():
    assert legacy_analyse._TACHES_VERS_FOURNISSEUR[legacy_analyse.TypeTache.EXTRACTION] == "deepseek"
    assert legacy_analyse._TACHES_VERS_FOURNISSEUR[legacy_analyse.TypeTache.RESUME] == "deepseek"
    assert legacy_analyse._TACHES_VERS_FOURNISSEUR[legacy_analyse.TypeTache.INDEXATION] == "deepseek"


# --- _appeler_modele ----------------------------------------------------------

def test_appeler_modele_route_extraction_vers_deepseek_avec_les_bons_parametres(monkeypatch):
    fake = _FakeClientDeepseek('{"references": []}')
    monkeypatch.setattr(legacy_analyse, "_client_deepseek", lambda: fake)
    journaux = []
    monkeypatch.setattr(legacy_analyse.usage_log, "journaliser_usage", lambda *a: journaux.append(a))

    texte = legacy_analyse._appeler_modele(
        legacy_analyse.TypeTache.EXTRACTION, "system prompt", [{"role": "user", "content": "bonjour"}], 500,
    )

    assert texte == '{"references": []}'
    captured = fake.chat.completions.captured
    assert captured["model"] == legacy_analyse.MODEL_DEEPSEEK
    assert captured["max_tokens"] == 500
    assert captured["temperature"] == 0.2
    assert captured["seed"] == 42
    assert captured["extra_body"] == {"chat_template_kwargs": {"thinking": False}}
    assert captured["messages"][0] == {"role": "system", "content": "system prompt"}
    assert captured["messages"][1] == {"role": "user", "content": "bonjour"}
    assert journaux == [("deepseek", "extraction", legacy_analyse.MODEL_DEEPSEEK, 10, 5)]


def test_appeler_modele_route_analyse_vers_claude_sans_toucher_a_deepseek(monkeypatch):
    fake = _FakeClientClaude("réponse Claude")
    monkeypatch.setattr(legacy_analyse, "_client", lambda: fake)

    def _echoue_si_appelee():
        raise AssertionError("_client_deepseek ne doit jamais être appelée pour TypeTache.ANALYSE")

    monkeypatch.setattr(legacy_analyse, "_client_deepseek", _echoue_si_appelee)
    journaux = []
    monkeypatch.setattr(legacy_analyse.usage_log, "journaliser_usage", lambda *a: journaux.append(a))

    texte = legacy_analyse._appeler_modele(
        legacy_analyse.TypeTache.ANALYSE, "system", [{"role": "user", "content": "x"}], 300,
    )

    assert texte == "réponse Claude"
    assert fake.messages.captured["model"] == legacy_analyse.MODEL_ACTIF
    assert journaux == [("claude", "analyse", legacy_analyse.MODEL_ACTIF, 20, 8)]


# --- Fonctions migrées : extraire_elements_cles / resumer_dossier -----------

def test_extraire_elements_cles_utilise_le_type_tache_extraction(monkeypatch):
    appels = []

    def _espion(type_tache, system, messages, max_tokens):
        appels.append(type_tache)
        return '{"dates": [], "personnes_et_parties": [], "references": [], "demandes": [], "decisions": []}'

    monkeypatch.setattr(legacy_analyse, "_appeler_modele", _espion)
    legacy_analyse.extraire_elements_cles("un document")
    assert appels == [legacy_analyse.TypeTache.EXTRACTION]


def test_resumer_dossier_utilise_le_type_tache_resume(monkeypatch):
    appels = []

    def _espion(type_tache, system, messages, max_tokens):
        appels.append(type_tache)
        return '{"points_cles": [], "elements_manquants": []}'

    monkeypatch.setattr(legacy_analyse, "_appeler_modele", _espion)
    legacy_analyse.resumer_dossier("contenu du dossier")
    assert appels == [legacy_analyse.TypeTache.RESUME]


# --- Fonctions migrées : structuration (chronologie, PV, réquisitoire, ------
# --- rapport d'instruction, notes) -- extension demandée explicitement -----

@pytest.mark.parametrize(
    ("fonction", "reponse_json", "args"),
    [
        (legacy_analyse.construire_chronologie, '{"evenements": [], "elements_manquants": []}', ("contenu de l'affaire",)),
        (legacy_analyse.rediger_pv, "texte du PV", ("notes d'audience",)),
        (
            legacy_analyse.analyser_requisitoire,
            '{"qualification_retenue": "", "faits_et_elements_invoques": [], "circonstances_aggravantes": [], '
            '"circonstances_attenuantes": [], "peine_requise": "non précisée", "points_attention": []}',
            ("texte du réquisitoire",),
        ),
        (
            legacy_analyse.analyser_rapport_instruction,
            '{"actes_instruction": [], "elements_a_charge": [], "elements_a_decharge": [], '
            '"mesures_ordonnees": [], "sens_propose": "non précisé", "points_attention": []}',
            ("texte du rapport",),
        ),
        (
            legacy_analyse.traiter_notes,
            '{"note_structuree": "", "actions_a_faire": [], "points_a_retenir": []}',
            ("notes brutes",),
        ),
    ],
)
def test_fonctions_de_structuration_utilisent_le_type_tache_structuration(monkeypatch, fonction, reponse_json, args):
    appels = []

    def _espion(type_tache, system, messages, max_tokens):
        appels.append(type_tache)
        return reponse_json

    monkeypatch.setattr(legacy_analyse, "_appeler_modele", _espion)
    fonction(*args)
    assert appels == [legacy_analyse.TypeTache.STRUCTURATION]


def test_generer_plan_plaidoirie_reste_sur_claude_sans_exception(monkeypatch):
    """Décision finale de l'utilisateur après plusieurs revirements (voir
    l'historique de conversation) : la génération de plaidoirie reste
    exclusivement sur Claude. Test de régression explicite sur ce point
    précis, pas seulement couvert par le verrouillage générique de
    TypeTache.GENERATION."""
    def _echoue_si_appelee(*a, **k):
        raise AssertionError("_appeler_modele ne doit pas être dans le chemin de generer_plan_plaidoirie")

    monkeypatch.setattr(legacy_analyse, "_appeler_modele", _echoue_si_appelee)
    monkeypatch.setattr(legacy_analyse, "_client", lambda: _FakeClientClaude('{"plan": [], "points_attention": []}'))
    legacy_analyse.generer_plan_plaidoirie("contexte du dossier", 15)


def test_analyser_conclusions_nappelle_jamais_appeler_modele(monkeypatch):
    """Preuve inverse explicite : une fonction d'analyse/génération continue
    d'appeler _client() directement, elle ne passe pas par le routeur."""
    def _echoue_si_appelee(*a, **k):
        raise AssertionError("_appeler_modele ne doit pas être dans le chemin de analyser_conclusions")

    monkeypatch.setattr(legacy_analyse, "_appeler_modele", _echoue_si_appelee)
    monkeypatch.setattr(legacy_analyse, "_client", lambda: _FakeClientClaude('{"arguments": [], "points_attention": []}'))
    legacy_analyse.analyser_conclusions("texte de conclusions")


def test_analyser_paragraphe_reste_sur_claude_sans_exception(monkeypatch):
    """Même verrou que generer_plan_plaidoirie/analyser_conclusions ci-dessus :
    le mode paragraphe-par-paragraphe est aussi une fonction d'analyse
    d'arguments juridiques, elle n'a jamais de raison de passer par DeepSeek."""
    def _echoue_si_appelee(*a, **k):
        raise AssertionError("_appeler_modele ne doit pas être dans le chemin de analyser_paragraphe")

    monkeypatch.setattr(legacy_analyse, "_appeler_modele", _echoue_si_appelee)
    fake = _FakeClientClaude("[ANALYSE]\ntexte\n[STRATÉGIE]\ntexte\n[TEXTE PLAIDOIRIE]\ntexte")
    monkeypatch.setattr(legacy_analyse, "_client", lambda: fake)
    resultat = legacy_analyse.analyser_paragraphe("Un paragraphe de conclusions adverses.")
    assert fake.messages.captured["model"] == legacy_analyse.MODEL_ACTIF
    assert "[ANALYSE]" in resultat


# --- Garde dédié DeepSeek (app/demo.py) --------------------------------------

def test_exiger_cle_api_deepseek_leve_503_si_absente(monkeypatch):
    from app import demo

    monkeypatch.setattr(legacy_analyse, "cle_api_deepseek_configuree", lambda: False)
    with pytest.raises(HTTPException) as exc:
        demo.exiger_cle_api_deepseek()
    assert exc.value.status_code == 503


def test_exiger_cle_api_deepseek_ne_leve_rien_si_configuree(monkeypatch):
    from app import demo

    monkeypatch.setattr(legacy_analyse, "cle_api_deepseek_configuree", lambda: True)
    demo.exiger_cle_api_deepseek()  # ne lève rien


# --- Garde-fou d'entrée câblé sur les deux endpoints migrés ------------------

def test_extraction_appelle_le_garde_fou_dentree(client, monkeypatch):
    import app.routers.greffier as greffier_router
    from app import demo

    monkeypatch.setattr(demo, "mode_demo_effectif", lambda: False)
    monkeypatch.setattr(demo, "exiger_cle_api_deepseek", lambda: None)

    def _refuse(texte):
        raise DemandeRefusee("demande refusée par le test", "medium")

    monkeypatch.setattr(greffier_router, "executer_garde_fou", _refuse)

    reponse = client.post("/api/greffier/extraction", json={"texte": "x" * 30})
    assert reponse.status_code == 422


def test_resume_appelle_le_garde_fou_dentree(client, monkeypatch, dossier_demo_id):
    import app.routers.analyse as analyse_router
    from app import demo

    monkeypatch.setattr(demo, "mode_demo_effectif", lambda: False)
    monkeypatch.setattr(demo, "exiger_cle_api_deepseek", lambda: None)

    def _refuse(texte):
        raise DemandeRefusee("demande refusée par le test", "medium")

    monkeypatch.setattr(analyse_router.quality_pipeline, "executer_garde_fou", _refuse)

    reponse = client.post("/api/analyse/resume", json={"dossier_id": dossier_demo_id})
    assert reponse.status_code == 422


# --- Garde-fou d'entrée câblé sur les endpoints de structuration migrés -----

@pytest.mark.parametrize(
    ("chemin", "payload_supplementaire"),
    [
        ("/api/greffier/pv-audience", {"notes": "x" * 30}),
        ("/api/greffier/requisitoire", {"texte": "x" * 30}),
        ("/api/greffier/rapport-instruction", {"texte": "x" * 30}),
    ],
)
def test_endpoints_greffier_de_structuration_appellent_le_garde_fou_dentree(client, monkeypatch, chemin, payload_supplementaire):
    import app.routers.greffier as greffier_router
    from app import demo

    monkeypatch.setattr(demo, "mode_demo_effectif", lambda: False)
    monkeypatch.setattr(demo, "exiger_cle_api_deepseek", lambda: None)

    def _refuse(texte):
        raise DemandeRefusee("demande refusée par le test", "medium")

    monkeypatch.setattr(greffier_router, "executer_garde_fou", _refuse)

    reponse = client.post(chemin, json=payload_supplementaire)
    assert reponse.status_code == 422


def test_chronologie_appelle_le_garde_fou_dentree(client, monkeypatch, dossier_demo_id):
    import app.routers.greffier as greffier_router
    from app import demo

    monkeypatch.setattr(demo, "mode_demo_effectif", lambda: False)
    monkeypatch.setattr(demo, "exiger_cle_api_deepseek", lambda: None)

    def _refuse(texte):
        raise DemandeRefusee("demande refusée par le test", "medium")

    monkeypatch.setattr(greffier_router, "executer_garde_fou", _refuse)

    reponse = client.post("/api/greffier/chronologie", json={"dossier_id": dossier_demo_id})
    assert reponse.status_code == 422


def test_creer_note_appelle_le_garde_fou_dentree(client, monkeypatch, dossier_demo_id):
    import app.routers.notes as notes_router
    from app import demo

    monkeypatch.setattr(demo, "mode_demo_effectif", lambda: False)
    monkeypatch.setattr(demo, "exiger_cle_api_deepseek", lambda: None)

    def _refuse(texte):
        raise DemandeRefusee("demande refusée par le test", "medium")

    monkeypatch.setattr(notes_router, "executer_garde_fou", _refuse)

    reponse = client.post("/api/notes/", json={"dossier_id": dossier_demo_id, "note_brute": "x" * 30})
    assert reponse.status_code == 422
