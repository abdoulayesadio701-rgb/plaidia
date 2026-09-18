"""Tests du bilan d'entraînement chronométré (app/entrainement.py + /api/entrainement)."""

from app import entrainement
from fastapi.testclient import TestClient


def test_statut_dans_les_temps_avec_tolerance_de_10_pourcent():
    # 300 s alloués -> tolérance 30 s
    assert entrainement.statut_section(300, 329, True) == entrainement.DANS_LES_TEMPS
    assert entrainement.statut_section(300, 331, True) == entrainement.DEPASSE
    assert entrainement.statut_section(300, 271, True) == entrainement.DANS_LES_TEMPS
    assert entrainement.statut_section(300, 269, True) == entrainement.EN_AVANCE


def test_tolerance_minimale_de_10_secondes_pour_les_sections_courtes():
    # 30 s alloués -> 10 % = 3 s, relevé à 10 s
    assert entrainement.statut_section(30, 40, True) == entrainement.DANS_LES_TEMPS
    assert entrainement.statut_section(30, 41, True) == entrainement.DEPASSE


def test_section_non_traitee():
    assert entrainement.statut_section(120, 0, False) == entrainement.NON_TRAITE


def test_bilan_totaux_ne_comptent_que_les_sections_traitees():
    bilan = entrainement.construire_bilan([
        {"point": "Faits", "alloue_secondes": 300, "reel_secondes": 360, "traitee": True},
        {"point": "Droit", "alloue_secondes": 600, "reel_secondes": 540, "traitee": True},
        {"point": "Conclusion", "alloue_secondes": 120, "reel_secondes": 0, "traitee": False},
    ])
    assert bilan["total_alloue_secondes"] == 900
    assert bilan["total_reel_secondes"] == 900
    assert bilan["total_ecart_secondes"] == 0
    assert [s["statut"] for s in bilan["sections"]] == ["depasse", "dans_les_temps", "non_traite"]
    assert bilan["sections"][0]["ecart_secondes"] == 60
    assert bilan["sections"][2]["ecart_secondes"] == 0


def test_formater_duree():
    assert entrainement.formater_duree(125) == "2 min 05 s"
    assert entrainement.formater_duree(-45) == "-0 min 45 s"


def _sections():
    return [
        {"point": "Faits", "alloue_secondes": 300, "reel_secondes": 360, "traitee": True},
        {"point": "Droit", "alloue_secondes": 600, "reel_secondes": 540, "traitee": True},
    ]


def test_bilan_persiste_et_relu(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/entrainement/", json={"dossier_id": dossier_demo_id, "sections": _sections()})
    assert r.status_code == 200
    corps = r.json()
    assert corps["sections"][0]["statut"] == "depasse"
    assert corps["total_reel_secondes"] == 900
    assert corps["document_id"] is not None

    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "entrainement"})
    assert liste.json()[0]["id"] == corps["document_id"]
    assert liste.json()[0]["contenu"]["total_alloue_secondes"] == 900


def test_bilan_dossier_inconnu_404(client: TestClient):
    r = client.post("/api/entrainement/", json={"dossier_id": 999999, "sections": _sections()})
    assert r.status_code == 404


def test_bilan_liste_vide_422(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/entrainement/", json={"dossier_id": dossier_demo_id, "sections": []})
    assert r.status_code == 422


def test_bilan_duree_negative_422(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/entrainement/",
        json={"dossier_id": dossier_demo_id, "sections": [{"point": "X", "alloue_secondes": 10, "reel_secondes": -5}]},
    )
    assert r.status_code == 422


def test_export_bilan_word(client: TestClient, dossier_demo_id: int):
    bilan = client.post("/api/entrainement/", json={"dossier_id": dossier_demo_id, "sections": _sections()}).json()
    r = client.post(
        "/api/entrainement/export",
        json={
            "dossier_id": dossier_demo_id,
            "sections": bilan["sections"],
            "total_alloue_secondes": bilan["total_alloue_secondes"],
            "total_reel_secondes": bilan["total_reel_secondes"],
            "total_ecart_secondes": bilan["total_ecart_secondes"],
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r.content) > 0
