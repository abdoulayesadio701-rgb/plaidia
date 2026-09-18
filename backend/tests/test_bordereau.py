"""Tests du bordereau de pièces (app/bordereau.py + /api/bordereau)."""

import io

from app import bordereau
from docx import Document
from fastapi.testclient import TestClient


def test_extraire_sources_ignore_les_textes_colles_et_les_doublons():
    faits = (
        "Faits initiaux.\n\n"
        "--- Document importé le 12/03/2026 10:30 (contrat.pdf) ---\nTexte 1\n\n"
        "--- Document importé le 13/03/2026 09:00 (texte collé) ---\nTexte 2\n\n"
        "--- Document importé le 14/03/2026 11:15 (contrat.pdf) ---\nTexte 3\n\n"
        "--- Document importé le 15/03/2026 08:00 (lettre de mise en demeure.docx) ---\nTexte 4\n\n"
        "--- Document importé le 16/03/2026 08:00 ---\nSans nom"
    )
    assert bordereau.extraire_sources(faits) == ["contrat.pdf", "lettre de mise en demeure.docx"]


def test_extraire_sources_faits_vides():
    assert bordereau.extraire_sources("") == []
    assert bordereau.extraire_sources(None) == []


def test_formater_date():
    assert bordereau.formater_date("2026-03-12") == "12/03/2026"
    assert bordereau.formater_date("mars 2026") == "mars 2026"
    assert bordereau.formater_date("") == ""


def _pieces():
    return [
        {"numero": 2, "intitule": "Bulletins de salaire", "date": "2024-01-31", "produite_par": "Demandeur", "observation": "12 mois"},
        {"numero": 1, "intitule": "Contrat de travail", "date": "2022-05-02", "produite_par": "Demandeur"},
    ]


def test_bordereau_vide_par_defaut(client: TestClient, dossier_demo_id: int):
    r = client.get(f"/api/bordereau/{dossier_demo_id}")
    assert r.status_code == 200
    assert r.json() == {"pieces": [], "document_id": None}


def test_enregistrement_trie_par_numero_et_relit(client: TestClient, dossier_demo_id: int):
    r = client.put(f"/api/bordereau/{dossier_demo_id}", json={"pieces": _pieces()})
    assert r.status_code == 200
    assert [p["numero"] for p in r.json()["pieces"]] == [1, 2]

    relu = client.get(f"/api/bordereau/{dossier_demo_id}").json()
    assert relu["pieces"][0]["intitule"] == "Contrat de travail"
    assert relu["document_id"] == r.json()["document_id"]


def test_enregistrements_successifs_mettent_a_jour_le_meme_document(client: TestClient, dossier_demo_id: int):
    premier = client.put(f"/api/bordereau/{dossier_demo_id}", json={"pieces": _pieces()}).json()
    second = client.put(f"/api/bordereau/{dossier_demo_id}", json={"pieces": _pieces()[:1]}).json()
    assert second["document_id"] == premier["document_id"]
    assert len(second["pieces"]) == 1

    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "bordereau"}).json()
    assert len(liste) == 1


def test_numeros_en_double_422(client: TestClient, dossier_demo_id: int):
    doublon = [_pieces()[0], {**_pieces()[1], "numero": 2}]
    r = client.put(f"/api/bordereau/{dossier_demo_id}", json={"pieces": doublon})
    assert r.status_code == 422


def test_piece_sans_intitule_ou_numero_invalide_422(client: TestClient, dossier_demo_id: int):
    assert client.put(f"/api/bordereau/{dossier_demo_id}", json={"pieces": [{"numero": 1, "intitule": ""}]}).status_code == 422
    assert client.put(f"/api/bordereau/{dossier_demo_id}", json={"pieces": [{"numero": 0, "intitule": "X"}]}).status_code == 422


def test_dossier_inconnu_404(client: TestClient):
    assert client.get("/api/bordereau/999999").status_code == 404
    assert client.put("/api/bordereau/999999", json={"pieces": []}).status_code == 404
    assert client.get("/api/bordereau/999999/export").status_code == 404


def test_sources_importees(client: TestClient, dossier_demo_id: int):
    client.post(f"/api/dossiers/{dossier_demo_id}/faits", json={"texte": "Contenu du contrat", "source": "contrat-bail.pdf"})
    client.post(f"/api/dossiers/{dossier_demo_id}/faits", json={"texte": "Texte tapé"})
    r = client.get(f"/api/bordereau/{dossier_demo_id}/sources")
    assert r.status_code == 200
    assert r.json() == ["contrat-bail.pdf"]


def test_export_word_est_un_tableau_avec_les_pieces(client: TestClient, dossier_demo_id: int):
    client.put(f"/api/bordereau/{dossier_demo_id}", json={"pieces": _pieces()})
    r = client.get(f"/api/bordereau/{dossier_demo_id}/export")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    tableau = Document(io.BytesIO(r.content)).tables[0]
    lignes = [[c.text for c in ligne.cells] for ligne in tableau.rows]
    assert lignes[0] == ["N°", "Intitulé de la pièce", "Date", "Produite par"]
    assert lignes[1] == ["1", "Contrat de travail", "02/05/2022", "Demandeur"]
    assert lignes[2][1] == "Bulletins de salaire\n12 mois"
    assert lignes[2][2] == "31/01/2024"


def test_export_bordereau_vide_ne_plante_pas(client: TestClient, dossier_demo_id: int):
    assert client.get(f"/api/bordereau/{dossier_demo_id}/export").status_code == 200
