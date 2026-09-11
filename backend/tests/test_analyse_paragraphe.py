"""
test_analyse_paragraphe.py — analyse.analyser_paragraphe / PARAGRAPHE_SYSTEM_PROMPT.

Mode paragraphe-par-paragraphe demandé explicitement par l'utilisateur,
complémentaire de analyser_conclusions (voir le commentaire au-dessus de
PARAGRAPHE_SYSTEM_PROMPT dans analyse.py) : sortie texte libre balisée
[ANALYSE]/[STRATÉGIE]/[TEXTE PLAIDOIRIE], pas de JSON -- donc aucun parsing
à tester ici, juste la construction du system prompt et la transmission du
paragraphe. Reste sur Claude sans exception (voir test_model_router.py::
test_analyser_paragraphe_reste_sur_claude_sans_exception pour le verrou dédié).
"""

import analyse as legacy_analyse


class _FakeContenu:
    def __init__(self, text: str):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str):
        self.content = [_FakeContenu(text)]


class _ClientEspion:
    """Capture le dernier appel (`system`, `messages`, `model`, `max_tokens`)
    sans appel réseau réel -- même idiome que test_i18n.py::_ClientEspion."""

    def __init__(self, text: str = "[ANALYSE]\ntexte\n[STRATÉGIE]\ntexte\n[TEXTE PLAIDOIRIE]\ntexte"):
        self.messages = self
        self._text = text
        self.dernier_appel: dict | None = None

    def create(self, **kwargs):
        self.dernier_appel = kwargs
        return _FakeResponse(self._text)


def test_le_prompt_se_termine_par_la_regle_de_balisage():
    assert legacy_analyse.PARAGRAPHE_SYSTEM_PROMPT.endswith(legacy_analyse.REGLE_BALISAGE_CITATIONS)


def test_analyser_paragraphe_transmet_le_paragraphe_tel_quel(monkeypatch):
    espion = _ClientEspion()
    monkeypatch.setattr(legacy_analyse, "_client", lambda: espion)
    legacy_analyse.analyser_paragraphe("Le défendeur invoque la prescription de l'article 2224 du Code civil.")
    assert espion.dernier_appel["messages"] == [
        {"role": "user", "content": "Le défendeur invoque la prescription de l'article 2224 du Code civil."}
    ]
    assert espion.dernier_appel["system"].startswith(legacy_analyse.PARAGRAPHE_SYSTEM_PROMPT)
    assert espion.dernier_appel["model"] == legacy_analyse.MODEL_ACTIF


def test_analyser_paragraphe_ajoute_le_contexte_recherche_si_fourni(monkeypatch):
    espion = _ClientEspion()
    monkeypatch.setattr(legacy_analyse, "_client", lambda: espion)
    legacy_analyse.analyser_paragraphe("Un paragraphe.", contexte_recherche="\n\nContexte live : ...")
    assert espion.dernier_appel["system"].endswith("Contexte live : ...")


def test_analyser_paragraphe_retourne_le_texte_brut_sans_parsing_json(monkeypatch):
    """Contrairement à analyser_conclusions/generer_plan_plaidoirie, aucun
    json.loads ici -- une réponse texte libre balisée doit ressortir telle
    quelle, espaces de bord retirés."""
    espion = _ClientEspion("  [ANALYSE]\nRAS\n[STRATÉGIE]\nRAS\n[TEXTE PLAIDOIRIE]\nRAS  ")
    monkeypatch.setattr(legacy_analyse, "_client", lambda: espion)
    resultat = legacy_analyse.analyser_paragraphe("Un paragraphe.")
    assert resultat == "[ANALYSE]\nRAS\n[STRATÉGIE]\nRAS\n[TEXTE PLAIDOIRIE]\nRAS"


def test_analyser_paragraphe_recoit_la_directive_de_langue(monkeypatch):
    espion = _ClientEspion()
    monkeypatch.setattr(legacy_analyse, "_client", lambda: espion)
    jeton = legacy_analyse.definir_langue_requete("en")
    try:
        legacy_analyse.analyser_paragraphe("Un paragraphe.")
    finally:
        legacy_analyse.reinitialiser_langue_requete(jeton)
    assert "write your entire response in English" in espion.dernier_appel["system"]
