"""Tests du rattachement optionnel des conversations aux dossiers."""

import sqlite3

import db
from fastapi.testclient import TestClient


def test_migration_conversations_chat_ajoute_dossier_id_sans_rattacher_lexistant(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(database_path)
    conn.executescript(
        """
        CREATE TABLE dossiers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, date_creation TEXT NOT NULL);
        CREATE TABLE conversations_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            contenu_json TEXT NOT NULL,
            date_creation TEXT NOT NULL,
            date_modification TEXT NOT NULL
        );
        INSERT INTO conversations_chat (titre, contenu_json, date_creation, date_modification)
        VALUES ('Conversation legacy', '[]', '2026-01-01', '2026-01-01');
        """
    )
    conn.close()

    monkeypatch.setattr(db, "DB_PATH", database_path)
    db.init_db()

    conn = db.get_connection()
    colonnes = {row["name"] for row in conn.execute("PRAGMA table_info(conversations_chat)")}
    conversation = conn.execute("SELECT dossier_id FROM conversations_chat WHERE id = 1").fetchone()
    conn.close()

    assert "dossier_id" in colonnes
    assert conversation["dossier_id"] is None


def test_creer_et_lister_conversations_d_un_dossier(client: TestClient, dossier_demo_id: int):
    creation = client.post(
        "/api/chat/conversations",
        json={
            "titre": "Question sur le dossier",
            "historique": [{"role": "user", "content": "Quel est le délai ?"}],
            "dossier_id": dossier_demo_id,
        },
    )

    assert creation.status_code == 201
    assert creation.json()["dossier_id"] == dossier_demo_id

    liste = client.get(f"/api/chat/conversations/dossier/{dossier_demo_id}")
    assert liste.status_code == 200
    assert [conversation["id"] for conversation in liste.json()] == [creation.json()["id"]]
    assert liste.json()[0]["dossier_id"] == dossier_demo_id


def test_conversation_sans_dossier_reste_possible(client: TestClient, dossier_demo_id: int):
    creation = client.post(
        "/api/chat/conversations",
        json={
            "titre": "Question générale",
            "historique": [{"role": "user", "content": "Quelle est la règle ?"}],
        },
    )

    assert creation.status_code == 201
    assert creation.json()["dossier_id"] is None
    assert client.get(f"/api/chat/conversations/dossier/{dossier_demo_id}").json() == []


def test_creation_conversation_refuse_un_dossier_inconnu(client: TestClient):
    creation = client.post(
        "/api/chat/conversations",
        json={
            "titre": "Question impossible",
            "historique": [{"role": "user", "content": "Question"}],
            "dossier_id": 999999,
        },
    )

    assert creation.status_code == 404