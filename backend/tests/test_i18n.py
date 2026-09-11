"""
test_i18n.py — Internationalisation FR/EN (voir analyse._directive_langue,
backend/app/main.py::langue_requete_middleware, frontend/src/i18n).

Deux niveaux, comme pour la clé API personnelle (voir
test_chat_contextuel.py) :
- un test unitaire direct sur le ContextVar + la directive de langue ;
- un test HTTP bout en bout prouvant que l'en-tête X-Langue envoyé par le
  front (voir frontend/src/api/http.ts) atteint bien le ContextVar via le
  vrai middleware -- jamais en manipulant le ContextVar directement pour
  ce second cas, qui ne survivrait pas au middleware réel.
"""

import analyse as legacy_analyse
from fastapi.testclient import TestClient

from app.main import app

_HEADERS_CLE_TEST = {"x-anthropic-api-key": "sk-ant-cle-de-test"}


class _FakeContenu:
    def __init__(self, text: str):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str):
        self.content = [_FakeContenu(text)]


class _ClientEspion:
    """Capture le `system` reçu par le dernier appel -- pour vérifier que
    la directive de langue y a bien été ajoutée, sans appel réseau réel."""

    def __init__(self, text: str = "{}"):
        self.messages = self
        self._text = text
        self.dernier_system: str | None = None

    def create(self, **kwargs):
        self.dernier_system = kwargs.get("system")
        return _FakeResponse(self._text)


def test_langue_par_defaut_est_le_francais_sans_directive():
    assert legacy_analyse.langue_requete() == "fr"
    assert legacy_analyse._directive_langue() == ""


def test_valeur_de_langue_non_reconnue_retombe_sur_le_francais():
    jeton = legacy_analyse.definir_langue_requete("es")
    try:
        assert legacy_analyse.langue_requete() == "fr"
        assert legacy_analyse._directive_langue() == ""
    finally:
        legacy_analyse.reinitialiser_langue_requete(jeton)


def test_directive_anglaise_ajoutee_au_system_prompt_de_l_agent_principal(monkeypatch):
    """analyser_conclusions fait partie des agents couverts par la
    directive de langue (voir analyse.py, injection systématique sur les
    fonctions utilisées par analyse/plan/simulateur/consultation/greffier/
    chat)."""
    espion = _ClientEspion('{"arguments": [], "points_attention": []}')
    monkeypatch.setattr(legacy_analyse, "_client", lambda: espion)
    jeton = legacy_analyse.definir_langue_requete("en")
    try:
        legacy_analyse.analyser_conclusions("Texte de conclusions à analyser pour ce test.")
    finally:
        legacy_analyse.reinitialiser_langue_requete(jeton)
    assert "write your entire response in English" in espion.dernier_system
    assert "never translate a citation" in espion.dernier_system


def test_garde_fou_verificateur_critique_et_strategie_recoivent_la_directive(monkeypatch):
    """Couvre spécifiquement les agents nommés par la consigne : le
    garde-fou, le vérificateur, le critique et la stratégie combative
    doivent tous produire leurs messages dans la langue choisie."""
    espion = _ClientEspion("{}")
    monkeypatch.setattr(legacy_analyse, "_client", lambda: espion)
    jeton = legacy_analyse.definir_langue_requete("en")
    try:
        legacy_analyse.evaluer_garde_fou_entree("Un texte de plus de vingt-cinq caractères pour dépasser le raccourci.")
        assert "write your entire response in English" in espion.dernier_system

        legacy_analyse.verifier_juridiquement("texte", [])
        assert "write your entire response in English" in espion.dernier_system

        legacy_analyse.critiquer_reponse("texte à critiquer")
        assert "write your entire response in English" in espion.dernier_system

        legacy_analyse.generer_strategie_combative("contexte", "Défendeur")
        assert "write your entire response in English" in espion.dernier_system
    finally:
        legacy_analyse.reinitialiser_langue_requete(jeton)


def test_francais_ne_reçoit_aucune_directive_ajoutee(monkeypatch):
    espion = _ClientEspion('{"arguments": [], "points_attention": []}')
    monkeypatch.setattr(legacy_analyse, "_client", lambda: espion)
    # Langue par défaut, pas besoin de la positionner explicitement.
    legacy_analyse.analyser_conclusions("Texte de conclusions à analyser pour ce test.")
    assert "LANGUAGE" not in espion.dernier_system


def test_entete_x_langue_atteint_le_contextvar_via_le_vrai_middleware(monkeypatch):
    """Bout en bout : l'en-tête X-Langue envoyé par le front (voir
    frontend/src/api/http.ts) doit atteindre analyse.langue_requete()
    pendant le traitement de la requête -- testé via une vraie requête
    HTTP, pas en manipulant le ContextVar à la main (voir l'en-tête de ce
    fichier)."""
    capture = {}

    def _espion_style(texte: str):
        capture["langue"] = legacy_analyse.langue_requete()
        return {
            "langage_de_couverture": [],
            "affirmations_absolues": [],
            "voix_passive_suspecte": [],
            "ruptures_registre": [],
            "synthese_strategique": "",
        }

    monkeypatch.setattr(legacy_analyse, "analyser_style_adverse", _espion_style)
    client = TestClient(app)
    reponse = client.post(
        "/api/analyse/style",
        json={"texte": "Un texte quelconque à analyser pour ce test d'internationalisation."},
        headers={**_HEADERS_CLE_TEST, "x-langue": "en"},
    )
    assert reponse.status_code == 200
    assert capture["langue"] == "en"
    # La langue ne doit jamais fuiter sur la requête suivante qui n'en envoie pas.
    assert legacy_analyse.langue_requete() == "fr"
