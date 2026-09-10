"""Tests des épingles vers tous les éléments persistés."""

import sqlite3

import db
from fastapi.testclient import TestClient


def test_migration_conserve_les_epingles_existantes(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(database_path)
    conn.executescript(
        """
        CREATE TABLE dossiers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, date_creation TEXT NOT NULL);
        CREATE TABLE elements_epingles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            reference_id INTEGER NOT NULL,
            dossier_id INTEGER,
            libelle TEXT NOT NULL,
            date_creation TEXT NOT NULL
        );
        INSERT INTO dossiers (id, nom, date_creation) VALUES (1, 'Dossier existant', '2026-01-01');
        INSERT INTO elements_epingles (type, reference_id, dossier_id, libelle, date_creation)
        VALUES ('dossier', 1, 1, 'Dossier existant', '2026-01-01');
        """
    )
    conn.close()
    monkeypatch.setattr(db, "DB_PATH", database_path)
    db.init_db()
    assert len(db.lister_epingles()) == 1


def test_epinglage_documents_et_conversations(client: TestClient, dossier_demo_id: int):
    document = client.post("/api/analyse/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 15}).json()
    conversation = client.post(
        "/api/chat/conversations",
        json={"titre": "Conversation utile", "historique": [{"role": "user", "content": "Question"}], "dossier_id": dossier_demo_id},
    ).json()

    for type_element, reference_id, libelle in (
        ("document_genere", document["document_id"], "Plan sauvegardé"),
        ("conversation", conversation["id"], "Conversation utile"),
    ):
        response = client.post(
            "/api/epingles/",
            json={"type": type_element, "reference_id": reference_id, "dossier_id": dossier_demo_id, "libelle": libelle},
        )
        assert response.status_code == 201
        assert response.json()["type"] == type_element

    types = {pin["type"] for pin in client.get("/api/epingles/").json()}
    assert {"document_genere", "conversation"}.issubset(types)


def test_cible_inexistante_refusee(client: TestClient, dossier_demo_id: int):
    response = client.post(
        "/api/epingles/",
        json={"type": "document_genere", "reference_id": 999999, "dossier_id": dossier_demo_id, "libelle": "Fantôme"},
    )
    assert response.status_code == 404


def test_epingle_document_supprimee_oubliee_a_la_liste(client: TestClient, dossier_demo_id: int):
    document = client.post("/api/analyse/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 10}).json()
    pin = client.post(
        "/api/epingles/",
        json={"type": "document_genere", "reference_id": document["document_id"], "dossier_id": dossier_demo_id, "libelle": "Plan"},
    ).json()
    client.delete(f"/api/dossiers/{dossier_demo_id}")
    assert not any(item["id"] == pin["id"] for item in client.get("/api/epingles/").json())
