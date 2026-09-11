"""
test_demo_mode.py — Tests minimaux de l'API en mode démo (voir
backend/app/demo.py). Portée volontairement réduite : vérifie que les
actions démonstratives répondent avec des données cannées cohérentes avec
leurs schémas, que les actions non couvertes sont bloquées proprement
(503), et que les protections anti-abus de base (taille de texte) sont
actives -- pas une couverture exhaustive de toutes les routes de l'API.

Tout tourne sur une base SQLite jetable (voir conftest.py) : ces tests
n'appellent jamais l'API Anthropic et ne touchent jamais une base de
données réelle.
"""

import json

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_config_signale_le_mode_demo(client: TestClient):
    r = client.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert data["demo_mode"] is True
    assert data["dossier_demo_nom"] == "Diallo c/ Atlas Logistique"
    assert data["max_texte_caracteres"] > 0


def test_dossier_demo_ensemence_automatiquement(client: TestClient):
    r = client.get("/api/dossiers/")
    assert r.status_code == 200
    dossiers = r.json()
    assert len(dossiers) == 1
    assert dossiers[0]["nom"] == "Diallo c/ Atlas Logistique"
    assert dossiers[0]["domaine"] == "Prud'hommes"


def test_analyser_conclusions_renvoie_les_donnees_cannees(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/conclusions", json={"texte": "peu importe le contenu envoyé", "dossier_id": dossier_demo_id})
    assert r.status_code == 200
    data = r.json()
    assert len(data["arguments"]) == 3
    premier = data["arguments"][0]
    assert premier["risque"] in ("Faible", "Moyen", "Élevé")
    assert premier["raisonnement"] is not None
    assert "probleme_de_droit" in premier["raisonnement"]
    # Jamais persistée en mode démo -- voir demo.py et le bandeau "données
    # non conservées".
    assert data["analyse_id"] is None


def test_analyser_conclusions_sans_dossier_fonctionne_aussi(client: TestClient):
    r = client.post("/api/analyse/conclusions", json={"texte": "texte quelconque"})
    assert r.status_code == 200
    assert len(r.json()["arguments"]) == 3


def test_plan_de_plaidoirie_canne(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 15})
    assert r.status_code == 200
    data = r.json()
    assert data["accroche"]
    assert len(data["plan"]) >= 1
    assert all("point" in p and "argument_cle" in p for p in data["plan"])


def test_simulateur_objections_canne(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/simulateur", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    data = r.json()
    assert len(data["objections"]) >= 1
    assert data["point_le_plus_faible"]


def test_resume_dossier_canne(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/resume", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    data = r.json()
    assert data["resume_court"]
    assert len(data["points_cles"]) >= 1


def test_chronologie_cannee(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/greffier/chronologie", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    data = r.json()
    assert data["periode_couverte"]
    assert len(data["evenements"]) >= 1
    assert all("date" in e and "evenement" in e for e in data["evenements"])


def test_dossier_inconnu_renvoie_404_meme_en_mode_demo(client: TestClient):
    r = client.post("/api/analyse/plan", json={"dossier_id": 999999, "temps_minutes": 10})
    assert r.status_code == 404


def test_action_non_cannee_est_bloquee_en_mode_demo(client: TestClient):
    """/api/analyse/style n'a pas de réponse préenregistrée -- doit
    échouer proprement en 503 plutôt que de tenter (et rater) un vrai
    appel à Claude sans clé API."""
    r = client.post("/api/analyse/style", json={"texte": "un texte quelconque à analyser"})
    assert r.status_code == 503
    assert "detail" in r.json()
    assert "mode démo" in r.json()["detail"].lower()


def test_extraction_greffier_bloquee_en_mode_demo(client: TestClient):
    r = client.post("/api/greffier/extraction", json={"texte": "un texte quelconque"})
    assert r.status_code == 503


def test_intention_degrade_proprement_en_mode_demo(client: TestClient):
    """Pas de 503 ici par choix (voir intention.py) : la CommandBar sait
    déjà orienter l'utilisateur vers la sidebar sur confiance basse."""
    r = client.post("/api/intention/interpreter", json={"texte": "analyser ces conclusions"})
    assert r.status_code == 200
    data = r.json()
    assert data["action"] == "menu"
    assert data["confiance"] == "basse"


def test_texte_trop_long_est_rejete(client: TestClient):
    r = client.get("/api/config")
    limite = r.json()["max_texte_caracteres"]
    r2 = client.post("/api/analyse/conclusions", json={"texte": "a" * (limite + 1)})
    assert r2.status_code == 422


def test_texte_sous_la_limite_est_accepte(client: TestClient):
    r = client.post("/api/analyse/conclusions", json={"texte": "a" * 100})
    assert r.status_code == 200


def test_chat_stream_reste_en_mode_demo_et_contient_le_marqueur(client: TestClient):
    r = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "Quelle est la différence entre faute grave et faute simple ?"}]},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    assert "event: done" in r.text

    # La balise [VERIF:...] (remplace l'ancien marqueur libre "À VÉRIFIER",
    # voir analyse.REGLE_BALISAGE_CITATIONS) peut être coupée entre deux
    # trames "delta" -- exactement pourquoi RichOutput.tsx recompose le
    # texte accumulé côté front plutôt que de chercher la sous-chaîne dans
    # chaque fragment brut. On reproduit cette recomposition ici plutôt que
    # de chercher la sous-chaîne dans le flux SSE brut, ce qui échouerait à
    # tort.
    texte_reconstitue = "".join(
        json.loads(bloc.split("data:", 1)[1])["text"]
        for bloc in r.text.split("\n\n")
        if bloc.startswith("event: delta")
    )
    assert "[VERIF:" in texte_reconstitue


def test_chat_contextuel_bloque_en_mode_demo(client: TestClient):
    """/api/chat/contextuel n'a pas de réponse préenregistrée -- même
    garde-fou que /api/analyse/style (voir test_action_non_cannee_est_bloquee_en_mode_demo)."""
    r = client.post(
        "/api/chat/contextuel",
        json={"feature": "conclusions", "resultat_actuel": {"arguments": []}, "message": "développe le premier argument"},
    )
    assert r.status_code == 503
    assert "mode démo" in r.json()["detail"].lower()


def test_cle_personnelle_desactive_le_mode_demo_effectif(client: TestClient):
    """Vérifie le mécanisme de contournement du mode démo directement
    (sans passer par un vrai appel réseau à Anthropic, qu'une clé bidon
    ferait de toute façon échouer plus loin et rendrait ce test lent et
    dépendant du réseau pour rien) : voir analyse.py::definir_cle_api_requete
    et demo.py::mode_demo_effectif."""
    import analyse as legacy_analyse
    from app import demo

    assert demo.mode_demo_effectif() is True

    jeton = legacy_analyse.definir_cle_api_requete("sk-ant-cle-de-test")
    try:
        assert demo.mode_demo_effectif() is False
    finally:
        legacy_analyse.reinitialiser_cle_api_requete(jeton)

    assert demo.mode_demo_effectif() is True
