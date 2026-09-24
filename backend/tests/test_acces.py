"""Mot de passe d'accès optionnel (voir backend/app/acces.py)."""

import pytest
from fastapi.testclient import TestClient

EN_TETE = "x-acces-mot-de-passe"


@pytest.fixture()
def protege(monkeypatch):
    monkeypatch.setenv("ACCESS_PASSWORD", "sesame-de-test")


def test_sans_mot_de_passe_configure_rien_ne_change(client: TestClient):
    assert client.get("/api/config").json()["acces_protege"] is False
    assert client.get("/api/dossiers/").status_code == 200
    assert client.post("/api/acces/verifier").status_code == 204


def test_config_signale_que_l_acces_est_protege(client: TestClient, protege):
    assert client.get("/api/config").json()["acces_protege"] is True


def test_routes_libres_restent_accessibles_sans_mot_de_passe(client: TestClient, protege):
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/config").status_code == 200


def test_route_protegee_refuse_sans_mot_de_passe(client: TestClient, protege):
    r = client.get("/api/dossiers/")
    assert r.status_code == 401
    assert "mot de passe" in r.json()["detail"].lower()


def test_route_protegee_refuse_un_mauvais_mot_de_passe(client: TestClient, protege):
    assert client.get("/api/dossiers/", headers={EN_TETE: "mauvais"}).status_code == 401
    assert client.post("/api/acces/verifier", headers={EN_TETE: "mauvais"}).status_code == 401


def test_route_protegee_accepte_le_bon_mot_de_passe(client: TestClient, protege):
    assert client.get("/api/dossiers/", headers={EN_TETE: "sesame-de-test"}).status_code == 200
    assert client.post("/api/acces/verifier", headers={EN_TETE: "sesame-de-test"}).status_code == 204


def test_le_chat_en_streaming_est_protege(client: TestClient, protege):
    corps = {"messages": [{"role": "user", "content": "bonjour"}]}
    assert client.post("/api/chat/stream", json=corps).status_code == 401
    ok = client.post("/api/chat/stream", json=corps, headers={EN_TETE: "sesame-de-test"})
    assert ok.status_code == 200


def test_le_refus_garde_les_en_tetes_cors(client: TestClient, protege):
    """Sans en-têtes CORS, le navigateur ne pourrait pas lire la 401 et le
    formulaire du front ne saurait pas qu'il doit s'afficher."""
    origine = "http://localhost:5173"
    r = client.get("/api/dossiers/", headers={"Origin": origine})
    assert r.status_code == 401
    assert r.headers.get("access-control-allow-origin") == origine


def test_le_preflight_cors_n_exige_pas_le_mot_de_passe(client: TestClient, protege):
    r = client.options(
        "/api/dossiers/",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.status_code == 200


def test_mot_de_passe_reduit_a_des_espaces_equivaut_a_aucun(client: TestClient, monkeypatch):
    monkeypatch.setenv("ACCESS_PASSWORD", "   ")
    assert client.get("/api/config").json()["acces_protege"] is False
    assert client.get("/api/dossiers/").status_code == 200
