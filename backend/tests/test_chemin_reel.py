"""Chemin RÉEL (hors mode démo) des endpoints qui ont une réponse démo
(app/demo_data_outils.py). Le mode démo répond avant tout appel à analyse.py ;
ces tests prouvent que, avec une clé personnelle (en-tête
x-anthropic-api-key), la requête traverse toujours le vrai analyseur -- ici
remplacé par un double pour ne consommer aucun appel modèle -- et que sa
sortie est renvoyée telle quelle, pas la réponse préenregistrée."""

import analyse as legacy_analyse
import pytest
from app import quality_pipeline
from app.routers import greffier as routeur_greffier
from app.routers import notes as routeur_notes
from fastapi.testclient import TestClient

CLE = {"x-anthropic-api-key": "sk-ant-test"}
TEXTE = "Le 12 mars 2024, M. Karim Diallo a saisi le tribunal."


@pytest.fixture(autouse=True)
def sans_appel_modele(monkeypatch):
    """Neutralise les gardes qui appelleraient un vrai modèle."""
    monkeypatch.setattr(quality_pipeline, "executer_garde_fou", lambda *a, **k: None)
    monkeypatch.setattr(routeur_greffier, "executer_garde_fou", lambda *a, **k: None)
    monkeypatch.setattr(routeur_notes, "executer_garde_fou", lambda *a, **k: None)
    monkeypatch.setattr(legacy_analyse, "cle_api_deepseek_configuree", lambda: True)


def test_sans_cle_l_extraction_repond_en_demo(client: TestClient):
    # Sans clé : réponse de démonstration (dates repérées par expression régulière),
    # à opposer aux tests ci-dessous qui, avec une clé, traversent le vrai analyseur.
    demo_reponse = client.post("/api/greffier/extraction", json={"texte": TEXTE}).json()
    assert demo_reponse["dates"] == ["12 mars 2024"]


def test_style_utilise_l_analyseur_reel(monkeypatch, client: TestClient):
    attendu = {"langage_de_couverture": [{"citation": "réel", "commentaire": "c"}], "affirmations_absolues": [],
               "voix_passive_suspecte": [], "ruptures_registre": [], "synthese_strategique": "synthèse réelle"}
    monkeypatch.setattr(legacy_analyse, "analyser_style_adverse", lambda texte: attendu)
    r = client.post("/api/analyse/style", json={"texte": TEXTE}, headers=CLE)
    assert r.status_code == 200 and r.json()["synthese_strategique"] == "synthèse réelle"


def test_traduction_utilise_l_analyseur_reel(monkeypatch, client: TestClient):
    monkeypatch.setattr(
        legacy_analyse, "traduire_texte",
        lambda texte: {"langue_detectee": "Français", "langue_cible": "English", "texte_traduit": "traduction réelle"},
    )
    r = client.post("/api/analyse/traduire", json={"texte": TEXTE}, headers=CLE)
    assert r.status_code == 200 and r.json()["texte_traduit"] == "traduction réelle"


def test_extraction_utilise_l_analyseur_reel(monkeypatch, client: TestClient):
    monkeypatch.setattr(
        legacy_analyse, "extraire_elements_cles",
        lambda texte: {"dates": ["date réelle"], "personnes_et_parties": [], "references": [], "demandes": [], "decisions": []},
    )
    r = client.post("/api/greffier/extraction", json={"texte": TEXTE}, headers=CLE)
    assert r.status_code == 200 and r.json()["dates"] == ["date réelle"]


def test_classement_utilise_l_analyseur_reel(monkeypatch, client: TestClient):
    monkeypatch.setattr(
        legacy_analyse, "classifier_document",
        lambda texte: {"nature": "ordonnance", "justification": "réelle", "confiance": "Élevée"},
    )
    r = client.post("/api/greffier/classement", json={"texte": TEXTE}, headers=CLE)
    assert r.status_code == 200 and r.json()["justification"] == "réelle"


def test_coherence_utilise_l_analyseur_reel(monkeypatch, client: TestClient):
    monkeypatch.setattr(
        legacy_analyse, "extraire_elements_cles",
        lambda texte: {"dates": [], "personnes_et_parties": [], "references": [], "demandes": [], "decisions": []},
    )
    monkeypatch.setattr(
        legacy_analyse, "controler_coherence",
        lambda elements: {"contradictions": [], "elements_coherents": ["cohérence réelle"], "limites_analyse": "limites réelles"},
    )
    r = client.post(
        "/api/greffier/coherence",
        json={"documents": [{"nom_document": "A", "texte": TEXTE}, {"nom_document": "B", "texte": TEXTE}]},
        headers=CLE,
    )
    assert r.status_code == 200 and r.json()["elements_coherents"] == ["cohérence réelle"]


def test_pv_audience_utilise_l_analyseur_reel(monkeypatch, client: TestClient):
    monkeypatch.setattr(legacy_analyse, "rediger_pv", lambda notes: "PV réel")
    r = client.post("/api/greffier/pv-audience", json={"notes": TEXTE}, headers=CLE)
    assert r.status_code == 200 and r.json()["texte"] == "PV réel"


def test_requisitoire_et_rapport_instruction_utilisent_l_analyseur_reel(monkeypatch, client: TestClient):
    monkeypatch.setattr(
        legacy_analyse, "analyser_requisitoire",
        lambda texte: {"qualification_retenue": "qualification réelle", "peine_requise": "peine réelle"},
    )
    monkeypatch.setattr(legacy_analyse, "analyser_rapport_instruction", lambda texte: {"sens_propose": "sens réel"})
    assert client.post("/api/greffier/requisitoire", json={"texte": TEXTE}, headers=CLE).json()["qualification_retenue"] == "qualification réelle"
    assert client.post("/api/greffier/rapport-instruction", json={"texte": TEXTE}, headers=CLE).json()["sens_propose"] == "sens réel"


def test_prise_de_note_utilise_l_analyseur_reel(monkeypatch, client: TestClient, dossier_demo_id: int):
    monkeypatch.setattr(
        legacy_analyse, "traiter_notes",
        lambda note: {"note_structuree": "structurée réelle", "actions_a_faire": ["action réelle"], "points_a_retenir": ["point réel"]},
    )
    r = client.post("/api/notes/", json={"dossier_id": dossier_demo_id, "note_brute": "peu importe"}, headers=CLE)
    assert r.status_code == 201
    assert r.json()["note_structuree"] == "structurée réelle" and r.json()["actions"] == ["action réelle"]


def test_le_garde_fou_deepseek_reste_actif_hors_demo(monkeypatch, client: TestClient):
    """Une clé personnelle Anthropic ne remplace pas le fournisseur DeepSeek :
    sans clé NVIDIA, extraction / PV / réquisitoire / rapport / note restent
    en 503 (ce n'est pas un mode démo, c'est un fournisseur absent)."""
    monkeypatch.setattr(legacy_analyse, "cle_api_deepseek_configuree", lambda: False)
    r = client.post("/api/greffier/extraction", json={"texte": TEXTE}, headers=CLE)
    assert r.status_code == 503
