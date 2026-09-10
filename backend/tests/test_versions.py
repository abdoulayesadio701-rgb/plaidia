"""
test_versions.py — Tests du versioning branché sur le chat contextuel (voir
AUDIT_TASKBAR.md, étape 4) : chaque patch appliqué via POST
/api/chat/contextuel doit créer une version, consultable via GET
/api/versions et restaurable via POST /api/versions/{id}/restaurer sans
jamais supprimer l'historique existant.

Même contournement du mode démo que test_chat_contextuel.py (en-tête
X-Anthropic-Api-Key) et même monkeypatch de traiter_message_edition --
seul le comportement de app.chat_actions + la persistance nous intéressent
ici, pas le jugement réel du modèle."""

import analyse as legacy_analyse
import pytest
from fastapi.testclient import TestClient

_HEADERS_CLE_TEST = {"x-anthropic-api-key": "sk-ant-cle-de-test"}


@pytest.fixture(autouse=True)
def _garde_fou_toujours_permissif(monkeypatch):
    monkeypatch.setattr(
        legacy_analyse,
        "evaluer_garde_fou_entree",
        lambda texte: {"allowed": True, "risk_level": "low", "reason": "", "requires_clarification": False},
    )


def _mocker_edition_modify(monkeypatch, scope="arguments[0]", contenu=None):
    monkeypatch.setattr(
        legacy_analyse,
        "traiter_message_edition",
        lambda **kwargs: {
            "intent": "modify",
            "scope": scope,
            "operation": "rewrite",
            "parameters": {},
            "contenu_modifie": contenu or {"resume": "Argument réécrit"},
            "reponse_agent": "Argument reformulé à votre demande.",
        },
    )


def _editer(client: TestClient, dossier_id: int) -> dict:
    r = client.post(
        "/api/chat/contextuel",
        json={
            "feature": "conclusions",
            "dossier_id": dossier_id,
            "resultat_actuel": {"arguments": [{"resume": "Original"}], "points_attention": []},
            "message": "réécris le premier argument",
        },
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    return r.json()


def test_une_edition_reussie_cree_une_version(client: TestClient, dossier_demo_id: int, monkeypatch):
    _mocker_edition_modify(monkeypatch)
    resultat = _editer(client, dossier_demo_id)
    assert resultat["resultat_modifie"] is not None

    r = client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier_demo_id})
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 1
    assert versions[0]["auteur"] == "ia"
    assert versions[0]["resume_modification"] == "Argument reformulé à votre demande."
    assert versions[0]["contenu"]["arguments"][0]["resume"] == "Argument réécrit"


def test_une_action_refusee_ne_cree_aucune_version(client: TestClient, dossier_demo_id: int, monkeypatch):
    _mocker_edition_modify(monkeypatch, scope="arguments[99]")  # index inexistant -- ActionInvalide
    resultat = _editer(client, dossier_demo_id)
    assert resultat["resultat_modifie"] is None

    versions = client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier_demo_id}).json()
    assert versions == []


def test_plusieurs_editions_saccumulent_les_plus_recentes_dabord(client: TestClient, dossier_demo_id: int, monkeypatch):
    _mocker_edition_modify(monkeypatch, contenu={"resume": "Version 1"})
    _editer(client, dossier_demo_id)
    _mocker_edition_modify(monkeypatch, contenu={"resume": "Version 2"})
    _editer(client, dossier_demo_id)

    versions = client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier_demo_id}).json()
    assert len(versions) == 2
    assert versions[0]["contenu"]["arguments"][0]["resume"] == "Version 2"  # la plus récente en premier
    assert versions[1]["contenu"]["arguments"][0]["resume"] == "Version 1"


def test_restaurer_ajoute_une_nouvelle_version_sans_rien_supprimer(client: TestClient, dossier_demo_id: int, monkeypatch):
    _mocker_edition_modify(monkeypatch, contenu={"resume": "Version 1"})
    _editer(client, dossier_demo_id)
    version_1_id = client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier_demo_id}).json()[0]["id"]

    _mocker_edition_modify(monkeypatch, contenu={"resume": "Version 2"})
    _editer(client, dossier_demo_id)

    r = client.post(f"/api/versions/{version_1_id}/restaurer")
    assert r.status_code == 200
    restauree = r.json()
    assert restauree["auteur"] == "utilisateur"
    assert restauree["contenu"]["arguments"][0]["resume"] == "Version 1"

    # Les 3 versions coexistent -- rien n'a été supprimé ni écrasé.
    versions = client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier_demo_id}).json()
    assert len(versions) == 3
    assert versions[0]["id"] == restauree["id"]  # la restauration est la plus récente


def test_restaurer_une_version_inexistante_404(client: TestClient):
    r = client.post("/api/versions/999999/restaurer")
    assert r.status_code == 404


def test_supprimer_le_dossier_supprime_ses_versions_en_cascade(client: TestClient, monkeypatch):
    dossier = client.post("/api/dossiers/", json={"nom": "Dossier temporaire versions"}).json()
    _mocker_edition_modify(monkeypatch)
    _editer(client, dossier["id"])
    assert len(client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier["id"]}).json()) == 1

    client.delete(f"/api/dossiers/{dossier['id']}")

    assert client.get("/api/versions/", params={"feature": "conclusions", "dossier_id": dossier["id"]}).json() == []
