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

    # Le header x-anthropic-api-key ci-dessous fait sortir la requête du mode
    # démo (voir main.py, "Utiliser ma propre clé Anthropic") : /consulter
    # passe alors par le pipeline complet (garde-fou + trio qualité, voir
    # quality_pipeline.executer_pipeline_complet), qui fait de vrais appels
    # réseau à l'API Anthropic avec une clé factice si on ne mocke pas les
    # quatre agents -- ça pendait au lieu d'échouer vite dans un environnement
    # sans accès réseau sortant (découvert via pytest-timeout : ce test
    # dépassait les 10s). Même mocks que _mocker_agents_qualite dans
    # test_quality_pipeline.py.
    monkeypatch.setattr(
        legacy_analyse,
        "evaluer_garde_fou_entree",
        lambda texte: {"allowed": True, "risk_level": "low", "reason": "Demande légitime.", "requires_clarification": False},
    )
    monkeypatch.setattr(legacy_analyse, "verifier_juridiquement", lambda *a, **k: {"statut_global": "A_VERIFIER", "elements": []})
    monkeypatch.setattr(legacy_analyse, "critiquer_reponse", lambda *a, **k: {"critiques": [], "synthese": ""})
    monkeypatch.setattr(
        legacy_analyse,
        "valider_finalement",
        lambda verif, crit: {"statut_global": "A_VERIFIER", "points_a_verifier": [], "points_forts": [], "synthese_utilisateur": "Synthèse."},
    )
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


def test_chronologie_persistee_et_relue(client: TestClient, dossier_demo_id: int):
    """La chronologie a une réponse préenregistrée en mode démo (voir
    demo_data.chronologie_demo) -- persistée comme plan/simulateur, sans
    avoir besoin de sortir du mode démo pour ce test."""
    response = client.post("/api/greffier/chronologie", json={"dossier_id": dossier_demo_id})
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    assert document_id is not None
    assert response.json()["statut"] == "Brouillon"

    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "chronologie"})
    assert liste.status_code == 200
    assert len(liste.json()) == 1
    assert liste.json()[0]["id"] == document_id

    suppression = client.delete(f"/api/documents-generes/{document_id}")
    assert suppression.status_code == 204
    liste_apres = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "chronologie"})
    assert liste_apres.json() == []


def test_note_client_persistee_et_relue(monkeypatch, client: TestClient, dossier_demo_id: int):
    """Sans réponse préenregistrée en mode démo (voir notes.py::rediger_note_client) --
    sort du mode démo via une clé personnelle factice, comme
    test_consultation_est_rattachee_au_dossier ci-dessus."""
    import analyse as legacy_analyse

    monkeypatch.setattr(legacy_analyse, "rediger_note_client", lambda contexte: "Texte de note client de test.")
    response = client.post(
        "/api/notes/note-client",
        json={"dossier_id": dossier_demo_id},
        headers={"x-anthropic-api-key": "sk-ant-test"},
    )
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    assert document_id is not None
    assert response.json()["statut"] == "Brouillon"

    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "note_client"})
    assert len(liste.json()) == 1
    assert liste.json()[0]["id"] == document_id


def test_verification_procedurale_persistee_et_relue(monkeypatch, client: TestClient, dossier_demo_id: int):
    """Même principe que test_note_client_persistee_et_relue ci-dessus --
    pas de réponse préenregistrée en mode démo pour cette fonctionnalité."""
    import analyse as legacy_analyse

    monkeypatch.setattr(
        legacy_analyse,
        "verifier_procedure",
        lambda contexte: {"echeances_identifiees": [], "actes_potentiellement_manquants": [], "points_attention": ["point"]},
    )
    response = client.post(
        "/api/greffier/verification-procedurale",
        json={"dossier_id": dossier_demo_id},
        headers={"x-anthropic-api-key": "sk-ant-test"},
    )
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    assert document_id is not None

    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "verification_procedurale"})
    assert len(liste.json()) == 1
    assert liste.json()[0]["id"] == document_id
