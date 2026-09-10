"""Tests du cycle de vie des conclusions persistées."""

import sqlite3

import analyse as legacy_analyse
import db
from fastapi.testclient import TestClient


def test_migration_analyses_ajoute_statut_brouillon(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(database_path)
    conn.executescript(
        """
        CREATE TABLE dossiers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, date_creation TEXT NOT NULL);
        CREATE TABLE analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            arguments_json TEXT NOT NULL,
            points_attention_json TEXT
        );
        INSERT INTO analyses (dossier_id, date, arguments_json, points_attention_json)
        VALUES (1, '2026-01-01', '[]', '[]');
        """
    )
    conn.close()

    monkeypatch.setattr(db, "DB_PATH", database_path)
    db.init_db()

    conn = db.get_connection()
    colonnes = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
    statut = conn.execute("SELECT statut FROM analyses WHERE id = 1").fetchone()["statut"]
    conn.close()

    assert "statut" in colonnes
    assert statut == "Brouillon"


def _creer_analyse(dossier_id: int) -> int:
    return db.save_analyse(dossier_id, [{"resume": "Argument"}], [])


def test_transitions_valides_et_trace_dans_historique(client: TestClient, dossier_demo_id: int):
    analyse_id = _creer_analyse(dossier_demo_id)
    for statut in ("En cours", "En révision", "Validé", "Final"):
        response = client.patch(f"/api/analyse/conclusions/{analyse_id}/statut", json={"statut": statut})
        assert response.status_code == 200
        assert response.json()["statut"] == statut

    historique = client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier_demo_id})
    assert historique.status_code == 200
    assert [version["contenu"]["statut"] for version in historique.json()[:4]] == [
        "Final",
        "Validé",
        "En révision",
        "En cours",
    ]


def test_transition_invalide_est_refusee(client: TestClient, dossier_demo_id: int):
    analyse_id = _creer_analyse(dossier_demo_id)
    response = client.patch(f"/api/analyse/conclusions/{analyse_id}/statut", json={"statut": "Validé"})

    assert response.status_code == 409
    assert "Transition impossible" in response.json()["detail"]


def test_final_est_lecture_seule(client: TestClient, dossier_demo_id: int, monkeypatch):
    analyse_id = _creer_analyse(dossier_demo_id)
    for statut in ("En cours", "En révision", "Validé", "Final"):
        assert client.patch(f"/api/analyse/conclusions/{analyse_id}/statut", json={"statut": statut}).status_code == 200

    response = client.patch(f"/api/analyse/conclusions/{analyse_id}/statut", json={"statut": "Validé"})
    assert response.status_code == 409
    assert "Final" in response.json()["detail"]

    monkeypatch.setattr(
        legacy_analyse,
        "traiter_message_edition",
        lambda **kwargs: {
            "intent": "modify",
            "scope": "arguments[0]",
            "operation": "rewrite",
            "parameters": {},
            "contenu_modifie": {"resume": "Modification interdite"},
            "reponse_agent": "Fait.",
        },
    )
    response = client.post(
        "/api/chat/contextuel",
        json={
            "feature": "conclusions",
            "resultat_actuel": {"analyse_id": analyse_id, "arguments": [{"resume": "Original"}], "points_attention": []},
            "message": "Réécris cet argument",
        },
        headers={"x-anthropic-api-key": "sk-ant-cle-de-test"},
    )
    assert response.status_code == 409
    assert "ne peut plus être modifiée" in response.json()["detail"]