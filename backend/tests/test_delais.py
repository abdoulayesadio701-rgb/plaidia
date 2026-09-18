"""Tests du suivi des délais de procédure (app/delais.py + /api/greffier/delais).

Les dates attendues ont été calculées à la main (jours de la semaine
vérifiés au calendrier), pas relues depuis le code testé.
"""

from datetime import date

from app import delais
from fastapi.testclient import TestClient


def test_paques():
    assert delais._paques(2024) == date(2024, 3, 31)
    assert delais._paques(2025) == date(2025, 4, 20)
    assert delais._paques(2026) == date(2026, 4, 5)


def test_delai_en_mois_echeance_un_dimanche_est_proroge_au_lundi():
    # 12 mars 2026 + 1 mois = dimanche 12 avril -> lundi 13 avril (art. 642 CPC)
    brute, effective = delais.calculer_echeance(delais.CATALOGUE["appel_civil"], date(2026, 3, 12))
    assert brute == date(2026, 4, 12)
    assert effective == date(2026, 4, 13)


def test_delai_en_mois_quantieme_absent_donne_le_dernier_jour_du_mois():
    # 31 janvier 2026 + 1 mois -> 28 février (samedi) -> lundi 2 mars
    brute, effective = delais.calculer_echeance(delais.CATALOGUE["appel_civil"], date(2026, 1, 31))
    assert brute == date(2026, 2, 28)
    assert effective == date(2026, 3, 2)


def test_delai_en_mois_annee_bissextile():
    brute, effective = delais.calculer_echeance(delais.CATALOGUE["appel_civil"], date(2024, 1, 31))
    assert brute == effective == date(2024, 2, 29)


def test_delai_en_mois_chevauche_l_annee():
    # 30 novembre 2026 + 2 mois = 30 janvier 2027 (samedi) -> lundi 1er février
    brute, effective = delais.calculer_echeance(delais.CATALOGUE["pourvoi_civil"], date(2026, 11, 30))
    assert brute == date(2027, 1, 30)
    assert effective == date(2027, 2, 1)


def test_delai_en_jours_franc_exclut_aussi_le_jour_d_echeance():
    # 2 juin 2026 + 5 jours francs = lundi 8 juin (et non dimanche 7)
    brute, effective = delais.calculer_echeance(delais.CATALOGUE["pourvoi_penal"], date(2026, 6, 2))
    assert brute == effective == date(2026, 6, 8)


def test_delai_en_jours_non_franc():
    # 4 mai 2026 + 10 jours = jeudi 14 mai = Ascension -> vendredi 15 mai
    brute, effective = delais.calculer_echeance(delais.CATALOGUE["appel_correctionnel"], date(2026, 5, 4))
    assert brute == date(2026, 5, 14)
    assert effective == date(2026, 5, 15)


def test_jours_feries_2026_contiennent_les_mobiles():
    feries = delais.jours_feries(2026)
    assert date(2026, 4, 6) in feries    # lundi de Pâques
    assert date(2026, 5, 14) in feries   # Ascension
    assert date(2026, 5, 25) in feries   # lundi de Pentecôte
    assert date(2026, 7, 14) in feries


def test_catalogue_endpoint(client: TestClient):
    r = client.get("/api/greffier/delais/catalogue")
    assert r.status_code == 200
    par_code = {d["code"]: d for d in r.json()}
    assert set(par_code) == set(delais.CATALOGUE)
    assert par_code["pourvoi_penal"]["duree"] == "5 jours francs"
    assert par_code["appel_civil"]["reference"] == "art. 538 CPC"


def test_calcul_persiste_et_relu(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/greffier/delais",
        json={
            "dossier_id": dossier_demo_id,
            "delais": [{"type": "appel_civil", "date_depart": "2026-03-12", "libelle": "Jugement du 2 mars"}],
        },
    )
    assert r.status_code == 200
    corps = r.json()
    assert corps["delais"][0]["date_echeance"] == "2026-04-13"
    assert corps["delais"][0]["proroge"] is True
    assert corps["avertissement"]
    assert corps["document_id"] is not None

    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "delais"})
    assert liste.status_code == 200
    assert liste.json()[0]["id"] == corps["document_id"]
    assert liste.json()[0]["contenu"]["delais"][0]["date_echeance"] == "2026-04-13"


def test_calcul_type_inconnu_422(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/greffier/delais",
        json={"dossier_id": dossier_demo_id, "delais": [{"type": "inexistant", "date_depart": "2026-03-12"}]},
    )
    assert r.status_code == 422


def test_calcul_date_invalide_422(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/greffier/delais",
        json={"dossier_id": dossier_demo_id, "delais": [{"type": "appel_civil", "date_depart": "pas une date"}]},
    )
    assert r.status_code == 422


def test_calcul_dossier_inconnu_404(client: TestClient):
    r = client.post(
        "/api/greffier/delais",
        json={"dossier_id": 999999, "delais": [{"type": "appel_civil", "date_depart": "2026-03-12"}]},
    )
    assert r.status_code == 404


def test_calcul_liste_vide_422(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/greffier/delais", json={"dossier_id": dossier_demo_id, "delais": []})
    assert r.status_code == 422


def test_export_delais_word(client: TestClient, dossier_demo_id: int):
    calcul = client.post(
        "/api/greffier/delais",
        json={"dossier_id": dossier_demo_id, "delais": [{"type": "pourvoi_civil", "date_depart": "2026-11-30"}]},
    ).json()
    r = client.post(
        "/api/greffier/delais/export",
        json={"dossier_id": dossier_demo_id, "delais": calcul["delais"], "avertissement": calcul["avertissement"]},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r.content) > 0
