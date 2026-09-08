"""
test_exports_manquants.py — Tests des 3 exports ajoutés lors de l'audit
import/export (AUDIT_IMPORT_EXPORT.md §B) : simulateur d'objections,
chronologie (CSV), vérification procédurale -- les seules fonctionnalités
de l'Arsenal/Greffier qui produisaient un résultat structuré sans jamais
pouvoir l'exporter.

Fonctionne en mode démo (voir conftest.py) : ces endpoints ne font aucun
appel Claude, seulement de la mise en forme + export.py.
"""

from fastapi.testclient import TestClient


def test_export_simulateur_word(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/analyse/simulateur/export",
        json={
            "dossier_id": dossier_demo_id,
            "objections": [
                {"origine": "Juge", "question": "Pourquoi ce délai ?", "piege": "Teste la rigueur procédurale", "piste_reponse": "Rappeler l'art. X"}
            ],
            "point_le_plus_faible": "L'absence de mise en demeure préalable.",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r.content) > 0


def test_export_simulateur_dossier_inconnu_404(client: TestClient):
    r = client.post("/api/analyse/simulateur/export", json={"dossier_id": 999999, "objections": []})
    assert r.status_code == 404


def test_export_chronologie_csv(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/greffier/chronologie/export",
        json={"dossier_id": dossier_demo_id, "evenements": [{"date": "12/03/2024", "evenement": "Assignation délivrée"}]},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    corps = r.content.decode("utf-8-sig")
    assert "Date" in corps and "Assignation délivrée" in corps


def test_export_verification_procedurale_word(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/greffier/verification-procedurale/export",
        json={
            "dossier_id": dossier_demo_id,
            "echeances_identifiees": [{"echeance": "Conclusions à déposer", "date": "01/06/2024", "statut": "À venir"}],
            "actes_potentiellement_manquants": ["Signification du jugement"],
            "points_attention": [],
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r.content) > 0
