"""Tests de la persistance commune des plans, simulateurs et consultations."""

import sqlite3

import db
from fastapi.testclient import TestClient


def test_migration_documents_generes_cree_la_table(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(database_path)
    conn.executescript(
        """
        CREATE TABLE dossiers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, date_creation TEXT NOT NULL);
        CREATE TABLE versions_document (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id INTEGER,
            feature TEXT NOT NULL,
            contenu_json TEXT NOT NULL,
            resume_modification TEXT,
            auteur TEXT NOT NULL,
            date_creation TEXT NOT NULL
        );
        """
    )
    conn.close()

    monkeypatch.setattr(db, "DB_PATH", database_path)
    db.init_db()

    conn = db.get_connection()
    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    versions = {row["name"] for row in conn.execute("PRAGMA table_info(versions_document)")}
    conn.close()

    assert "documents_generes" in tables
    assert "document_id" in versions


def test_creation_liste_et_reouverture_des_documents(client: TestClient, dossier_demo_id: int):
    plan = client.post("/api/analyse/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 15})
    simulateur = client.post("/api/analyse/simulateur", json={"dossier_id": dossier_demo_id})

    assert plan.status_code == 200
    assert simulateur.status_code == 200
    assert plan.json()["document_id"] is not None
    assert simulateur.json()["document_id"] is not None
    assert plan.json()["statut"] == "Brouillon"

    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes")
    assert liste.status_code == 200
    features = {document["feature"] for document in liste.json()}
    assert {"plan", "simulateur"}.issubset(features)

    plan_id = plan.json()["document_id"]
    reopened = client.get(f"/api/documents-generes/{plan_id}")
    assert reopened.status_code == 200
    assert reopened.json()["contenu"]["plan"]
    assert reopened.json()["parametres"]["temps_minutes"] == 15


def test_transitions_document_et_verrou_final(client: TestClient, dossier_demo_id: int):
    response = client.post("/api/analyse/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 10})
    document_id = response.json()["document_id"]

    for statut in ("En cours", "En révision", "Validé", "Final"):
        changement = client.patch(f"/api/documents-generes/{document_id}/statut", json={"statut": statut})
        assert changement.status_code == 200
        assert changement.json()["statut"] == statut

    invalide = client.patch(f"/api/documents-generes/{document_id}/statut", json={"statut": "Validé"})
    assert invalide.status_code == 409
    assert "Final" in invalide.json()["detail"]


def test_consultation_est_rattachee_au_dossier(monkeypatch, client: TestClient, dossier_demo_id: int):
    import analyse as legacy_analyse

    monkeypatch.setattr(legacy_analyse, "identifier_notions_juridiques", lambda question, but: {"mots_cles_recherche": [], "but": but})
    monkeypatch.setattr(legacy_analyse, "consulter_jurisprudence", lambda *args, **kwargs: "Réponse sauvegardée")
    response = client.post(
        "/api/jurisprudence/consulter",
        json={"dossier_id": dossier_demo_id, "question": "Question de droit", "but": "Préparer la plaidoirie", "source": "Autre source"},
        headers={"x-anthropic-api-key": "sk-ant-test"},
    )

    assert response.status_code == 200
    assert response.json()["document_id"] is not None
    assert response.json()["statut"] == "Brouillon"
