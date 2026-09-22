"""Tests de /api/veille -- notifications persistantes (jurisprudence +
lois) pour le backend web, portage de gui.py::DialogueNotificationsVeille
/ DialogueAlertesArticles (voir backend/app/veille.py, db.py sections
"Veille"). Mode démo (voir conftest.py) : la boucle périodique ne démarre
jamais et /api/veille/verifier est un no-op -- testé explicitement."""

import db
from app import demo
from app import veille as veille_serveur
from fastapi.testclient import TestClient


def test_notifications_vides_par_defaut(client: TestClient):
    reponse = client.get("/api/veille/notifications")
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees == {"jurisprudence": [], "lois": [], "rappel_ohada": None}


def test_verifier_en_mode_demo_ne_fait_rien(client: TestClient):
    """DEMO_MODE=true dans les tests (voir conftest.py) -- un déploiement
    de démonstration public ne doit jamais consommer le quota Judilibre/
    Légifrance."""
    assert demo.mode_demo_serveur() is True
    assert veille_serveur.executer_un_passage() is False

    reponse = client.post("/api/veille/verifier")
    assert reponse.status_code == 202


def test_verifier_hors_demo_appelle_les_deux_verifications(client: TestClient, monkeypatch):
    appels = []
    monkeypatch.setattr(demo, "mode_demo_serveur", lambda: False)
    monkeypatch.setattr(veille_serveur, "verifier_jurisprudence", lambda: appels.append("jurisprudence"))
    monkeypatch.setattr(veille_serveur, "verifier_lois", lambda: appels.append("lois"))

    assert veille_serveur.executer_un_passage() is True
    assert appels == ["jurisprudence", "lois"]


def test_deux_passages_ne_se_superposent_jamais(client: TestClient, monkeypatch):
    """Le verrou (_verification_en_cours) doit empêcher un second passage
    de démarrer pendant qu'un premier tourne encore."""
    monkeypatch.setattr(demo, "mode_demo_serveur", lambda: False)
    monkeypatch.setattr(veille_serveur, "verifier_lois", lambda: None)

    def verifier_jurisprudence_lente():
        # Tente un second passage PENDANT que celui-ci tient le verrou.
        assert veille_serveur.executer_un_passage() is False

    monkeypatch.setattr(veille_serveur, "verifier_jurisprudence", verifier_jurisprudence_lente)
    assert veille_serveur.executer_un_passage() is True


def test_alerte_jurisprudence_apparait_et_sacquitte(client: TestClient, dossier_demo_id: int):
    db.creer_alerte_jurisprudence(dossier_demo_id, "Cass. Crim. 12 mars 2024, n°23-80.001", "Résumé de test.", "https://judilibre.test")

    donnees = client.get("/api/veille/notifications").json()
    assert len(donnees["jurisprudence"]) == 1
    alerte = donnees["jurisprudence"][0]
    assert alerte["dossier_id"] == dossier_demo_id
    assert alerte["statut"] == "active"

    assert client.post(f"/api/veille/jurisprudence/{alerte['id']}/acquitter").status_code == 204
    assert client.get("/api/veille/notifications").json()["jurisprudence"] == []


def test_alerte_loi_apparait_et_sacquitte(client: TestClient, dossier_demo_id: int):
    db.creer_alerte_article(dossier_demo_id, "CP", "311-1", "VIGUEUR", "ABROGE", "2026-01-01", "https://legifrance.test")

    donnees = client.get("/api/veille/notifications").json()
    assert len(donnees["lois"]) == 1
    alerte = donnees["lois"][0]
    assert alerte["code"] == "CP"
    assert alerte["numero"] == "311-1"

    assert client.post(f"/api/veille/lois/{alerte['id']}/acquitter").status_code == 204
    assert client.get("/api/veille/notifications").json()["lois"] == []


def test_notifications_filtrees_par_dossier(client: TestClient, dossier_demo_id: int):
    autre = client.post("/api/dossiers/", json={"nom": "Autre dossier"}).json()
    db.creer_alerte_jurisprudence(dossier_demo_id, "Réf. dossier démo", "R.", "S.")
    db.creer_alerte_jurisprudence(autre["id"], "Réf. autre dossier", "R.", "S.")

    filtrees = client.get("/api/veille/notifications", params={"dossier_id": dossier_demo_id}).json()
    assert len(filtrees["jurisprudence"]) == 1
    assert filtrees["jurisprudence"][0]["dossier_id"] == dossier_demo_id

    toutes = client.get("/api/veille/notifications").json()
    assert len(toutes["jurisprudence"]) == 2


def test_creer_alerte_jurisprudence_ne_duplique_pas(client: TestClient, dossier_demo_id: int):
    db.creer_alerte_jurisprudence(dossier_demo_id, "Même référence", "R.", "S.")
    db.creer_alerte_jurisprudence(dossier_demo_id, "Même référence", "R.", "S.")
    donnees = client.get("/api/veille/notifications").json()
    assert len(donnees["jurisprudence"]) == 1


def test_marquer_ohada_verifie(client: TestClient):
    assert db.get_parametre("veille_ohada_derniere_verification") is None
    assert client.post("/api/veille/ohada/marquer-verifie").status_code == 204
    assert db.get_parametre("veille_ohada_derniere_verification") is not None
