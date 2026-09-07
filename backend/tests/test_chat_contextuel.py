"""
test_chat_contextuel.py — Tests du endpoint POST /api/chat/contextuel qui
n'ont pas besoin d'un vrai appel réseau à Claude : on simule la réponse du
modèle (monkeypatch de analyse.traiter_message_edition) pour vérifier que
le routeur applique bien la validation de app.chat_actions avant de
renvoyer quoi que ce soit — la garantie centrale du §12/§13 de
ARCHITECTURE_CHAT_CONTEXTUEL.md : le modèle propose, chat_actions dispose.

Le mode démo (actif dans toute la suite, voir conftest.py) est contourné
via l'en-tête X-Anthropic-Api-Key, exactement comme un vrai visiteur qui
fournit sa propre clé (voir main.py::cle_api_personnelle_middleware) — pas
en manipulant le ContextVar directement, qui ne survivrait pas au
middleware réel une fois la requête HTTP effectuée.

La vérification avec un vrai modèle (comportement réel de classification)
a été faite manuellement avec une clé API réelle pendant le développement
-- volontairement absente d'ici pour ne pas rendre la suite de tests
dépendante du réseau ni d'une clé API.
"""

import analyse as legacy_analyse
from fastapi.testclient import TestClient

_HEADERS_CLE_TEST = {"x-anthropic-api-key": "sk-ant-cle-de-test"}


def test_modification_locale_validee_est_appliquee(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        legacy_analyse,
        "traiter_message_edition",
        lambda **kwargs: {
            "intent": "modify",
            "scope": "arguments[0]",
            "operation": "rewrite",
            "parameters": {},
            "contenu_modifie": {"resume": "Argument réécrit"},
            "reponse_agent": "Fait.",
        },
    )
    r = client.post(
        "/api/chat/contextuel",
        json={
            "feature": "conclusions",
            "resultat_actuel": {"arguments": [{"resume": "Original"}], "points_attention": []},
            "message": "réécris le premier argument",
        },
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["intent"] == "modify"
    assert data["resultat_modifie"]["arguments"][0]["resume"] == "Argument réécrit"
    assert data["resultat_modifie"]["points_attention"] == []  # intact


def test_action_avec_index_invalide_n_est_jamais_appliquee(client: TestClient, monkeypatch):
    """Si le modèle invente un index qui n'existe pas dans le résultat
    actuel, le routeur ne plante pas et ne renvoie surtout pas un
    resultat_modifie corrompu -- il retombe sur une demande de clarification."""
    monkeypatch.setattr(
        legacy_analyse,
        "traiter_message_edition",
        lambda **kwargs: {
            "intent": "modify",
            "scope": "arguments[99]",  # n'existe pas
            "operation": "rewrite",
            "parameters": {},
            "contenu_modifie": {"resume": "..."},
            "reponse_agent": "Fait.",
        },
    )
    r = client.post(
        "/api/chat/contextuel",
        json={
            "feature": "conclusions",
            "resultat_actuel": {"arguments": [{"resume": "Original"}], "points_attention": []},
            "message": "réécris un argument",
        },
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200  # jamais une 500 -- l'erreur est gérée proprement
    data = r.json()
    assert data["intent"] == "clarification"
    assert data["resultat_modifie"] is None


def test_explication_ne_modifie_rien(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        legacy_analyse,
        "traiter_message_edition",
        lambda **kwargs: {
            "intent": "explain",
            "scope": "arguments[0]",
            "operation": "explain",
            "parameters": {},
            "contenu_modifie": None,
            "reponse_agent": "Voici pourquoi cet argument est risqué...",
        },
    )
    r = client.post(
        "/api/chat/contextuel",
        json={
            "feature": "conclusions",
            "resultat_actuel": {"arguments": [{"resume": "Original"}], "points_attention": []},
            "message": "pourquoi cet argument est risqué ?",
        },
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["resultat_modifie"] is None
    assert "risqué" in data["reponse_agent"]


def test_historique_transmis_a_la_classification(client: TestClient, monkeypatch):
    """Vérifie que l'historique envoyé par le front atteint bien
    analyse.traiter_message_edition -- condition nécessaire pour qu'une
    demande de suivi ("encore plus formel") puisse être résolue par
    rapport à l'échange précédent (voir §6 de la demande initiale)."""
    appels = []

    def _capture(**kwargs):
        appels.append(kwargs)
        return {
            "intent": "modify",
            "scope": "texte",
            "operation": "rewrite",
            "parameters": {},
            "contenu_modifie": "Version encore plus formelle.",
            "reponse_agent": "Fait.",
        }

    monkeypatch.setattr(legacy_analyse, "traiter_message_edition", _capture)

    historique_envoye = [
        {"role": "user", "content": "Rends le ton plus professionnel."},
        {"role": "assistant", "content": "Version modifiée."},
    ]
    r = client.post(
        "/api/chat/contextuel",
        json={
            "feature": "note_client",
            "resultat_actuel": {"texte": "Version modifiée."},
            "message": "Encore un peu plus formel.",
            "historique": historique_envoye,
        },
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    assert len(appels) == 1
    historique_recu = appels[0]["historique"]
    assert historique_recu == historique_envoye
    assert appels[0]["message"] == "Encore un peu plus formel."


def test_dossier_inconnu_renvoie_404(client: TestClient):
    r = client.post(
        "/api/chat/contextuel",
        json={
            "feature": "conclusions",
            "dossier_id": 999999,
            "resultat_actuel": {"arguments": []},
            "message": "peu importe",
        },
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 404
