"""
test_demo_mode.py — Tests minimaux de l'API en mode démo (voir
backend/app/demo.py). Portée volontairement réduite : vérifie que les
actions démonstratives répondent avec des données cannées cohérentes avec
leurs schémas, et que les protections anti-abus de base (taille de texte)
sont actives -- pas une couverture exhaustive de toutes les routes de l'API.
Les fonctions qui lisent le texte saisi ou ont un exemple fictif sont
couvertes dans test_demo_outils.py ; leur chemin réel (avec une clé
personnelle) dans test_chemin_reel.py.

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


def _evenements_sse(texte: str) -> dict[str, dict]:
    """Reconstitue {nom_evenement: data} à partir d'un flux SSE complet --
    un seul évènement de chaque nom attendu ici, contrairement à
    /api/chat/stream qui répète "delta" (voir test_chat_stream_...)."""
    evenements = {}
    for bloc in texte.split("\n\n"):
        if bloc.startswith("event: "):
            nom, _, reste = bloc.partition("\n")
            nom = nom.removeprefix("event: ")
            data = json.loads(reste.split("data:", 1)[1])
            evenements[nom] = data
    return evenements


def test_analyser_conclusions_stream_fonctionne_en_mode_demo(client: TestClient, dossier_demo_id: int):
    """Avant ce test, /conclusions/stream renvoyait une 400 en mode démo --
    ce qui cassait le clic "Analyser des conclusions adverses" depuis
    l'Arsenal pour un visiteur du dossier de démonstration. Le flux SSE
    doit désormais servir la même réponse cannée que /conclusions (voir le
    commentaire de analyser_conclusions_stream)."""
    r = client.post(
        "/api/analyse/conclusions/stream",
        json={"texte": "peu importe le contenu envoyé", "dossier_id": dossier_demo_id},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    evenements = _evenements_sse(r.text)
    assert "principal" in evenements
    assert len(evenements["principal"]["arguments"]) == 3
    assert "done" in evenements


def test_analyser_conclusions_cannees_en_anglais_si_x_langue_en(client: TestClient):
    """Comme le chat (voir test_chat_stream_demo_repond_en_anglais_si_x_langue_en),
    les autres actions cannées doivent elles aussi respecter X-Langue --
    voir demo_data.py::conclusions_demo()."""
    r = client.post("/api/analyse/conclusions", json={"texte": "peu importe"}, headers={"x-langue": "en"})
    assert r.status_code == 200
    data = r.json()
    assert "lateness" in data["arguments"][0]["resume"].lower()
    # Le token de risque reste un enum fixe, jamais traduit dans les données.
    assert data["arguments"][0]["risque"] in ("Faible", "Moyen", "Élevé")


def test_plan_de_plaidoirie_canne(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 15})
    assert r.status_code == 200
    data = r.json()
    assert data["accroche"]
    assert len(data["plan"]) >= 1
    assert all("point" in p and "argument_cle" in p for p in data["plan"])


def test_plan_de_plaidoirie_canne_en_anglais_si_x_langue_en(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 15}, headers={"x-langue": "en"})
    assert r.status_code == 200
    assert "notice" in r.json()["accroche"].lower() or "tribunal" in r.json()["accroche"].lower()


def test_plan_de_plaidoirie_stream_fonctionne_en_mode_demo(client: TestClient, dossier_demo_id: int):
    """Même correction que test_analyser_conclusions_stream_fonctionne_en_mode_demo,
    pour /plan/stream. Le plan démo reste persisté comme un vrai document
    généré (voir /api/analyse/plan non-stream), donc récupérable ensuite
    via GET /api/documents-generes/{id}."""
    r = client.post(
        "/api/analyse/plan/stream",
        json={"dossier_id": dossier_demo_id, "temps_minutes": 15},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    evenements = _evenements_sse(r.text)
    assert evenements["principal"]["accroche"]
    document_id = evenements["document"]["document_id"]
    assert document_id

    r2 = client.get(f"/api/documents-generes/{document_id}")
    assert r2.status_code == 200
    assert r2.json()["feature"] == "plan"


def test_simulateur_objections_canne(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/simulateur", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    data = r.json()
    assert len(data["objections"]) >= 1
    assert data["point_le_plus_faible"]


def test_simulateur_objections_canne_en_anglais_si_x_langue_en(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/simulateur", json={"dossier_id": dossier_demo_id}, headers={"x-langue": "en"})
    assert r.status_code == 200
    assert "diallo" in r.json()["point_le_plus_faible"].lower()
    assert "l'absence" not in r.json()["point_le_plus_faible"].lower()


def test_resume_dossier_canne(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/resume", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    data = r.json()
    assert data["resume_court"]
    assert len(data["points_cles"]) >= 1


def test_resume_dossier_canne_en_anglais_si_x_langue_en(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/analyse/resume", json={"dossier_id": dossier_demo_id}, headers={"x-langue": "en"})
    assert r.status_code == 200
    assert "warehouse operator" in r.json()["resume_court"].lower()


def test_chronologie_cannee(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/greffier/chronologie", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    data = r.json()
    assert data["periode_couverte"]
    assert len(data["evenements"]) >= 1
    assert all("date" in e and "evenement" in e for e in data["evenements"])


def test_chronologie_cannee_en_anglais_si_x_langue_en(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/greffier/chronologie", json={"dossier_id": dossier_demo_id}, headers={"x-langue": "en"})
    assert r.status_code == 200
    data = r.json()
    assert "hired" in data["evenements"][0]["evenement"].lower()


def test_dossier_inconnu_renvoie_404_meme_en_mode_demo(client: TestClient):
    r = client.post("/api/analyse/plan", json={"dossier_id": 999999, "temps_minutes": 10})
    assert r.status_code == 404


def test_style_repond_en_mode_demo(client: TestClient):
    """/api/analyse/style avait une 503 en mode démo ; il répond maintenant
    par un repérage simple des formules d'atténuation et absolues."""
    r = client.post("/api/analyse/style", json={"texte": "Il semblerait que le salarié ait manqué. Il n'a jamais contesté."})
    assert r.status_code == 200
    data = r.json()
    assert data["langage_de_couverture"] and data["affirmations_absolues"]
    assert data["synthese_strategique"]


def test_extraction_greffier_repond_en_mode_demo(client: TestClient):
    r = client.post("/api/greffier/extraction", json={"texte": "Le 12 mars 2024, M. Karim Diallo a saisi le tribunal."})
    assert r.status_code == 200
    data = r.json()
    assert data["dates"] == ["12 mars 2024"]
    assert data["personnes_et_parties"] == ["M. Karim Diallo"]


def test_intention_par_mots_cles_en_mode_demo(client: TestClient):
    """La barre de commande fonctionne en démo par mots-clés, sans modèle : son
    exemple affiché (« établir un plan de 10 minutes ») doit aboutir."""
    r = client.post("/api/intention/interpreter", json={"texte": "établir un plan de 10 minutes"})
    assert r.status_code == 200
    assert r.json() == {"action": "plan", "duree_minutes": 10, "confiance": "haute", "reformulation": "Compris : générer un plan de plaidoirie."}
    assert client.post("/api/intention/interpreter", json={"texte": "analyser ces conclusions"}).json()["action"] == "analyser"


def test_intention_inconnue_reste_orientee_vers_le_menu_en_mode_demo(client: TestClient):
    """Pas de 503 ici par choix (voir intention.py) : sans correspondance, la
    CommandBar sait orienter l'utilisateur vers la sidebar."""
    data = client.post("/api/intention/interpreter", json={"texte": "bonjour, quel temps fait-il ?"}).json()
    assert data["action"] == "menu" and data["confiance"] == "basse"


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


def test_chat_stream_demo_repond_en_anglais_si_x_langue_en(client: TestClient):
    """Contrairement aux autres actions cannées de ce fichier (figées en
    français), le chat démo doit respecter la langue d'interface -- voir
    app/demo_data.py::reponse_demo_pour_question et son commentaire d'en-tête."""
    r = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "Can you explain the serious misconduct claimed for this dismissal?"}]},
        headers={"x-langue": "en"},
    )
    assert r.status_code == 200
    texte_reconstitue = "".join(
        json.loads(bloc.split("data:", 1)[1])["text"]
        for bloc in r.text.split("\n\n")
        if bloc.startswith("event: delta")
    )
    # La version anglaise glose le terme français ("faute grave") entre
    # parenthèses à sa première mention -- elle n'en est pas moins bien en
    # anglais, contrairement à la réponse française d'origine.
    assert "serious misconduct" in texte_reconstitue.lower()
    assert "en droit du travail français" not in texte_reconstitue.lower()


def test_chat_contextuel_explique_le_mode_demo_sans_rien_modifier(client: TestClient):
    """/api/chat/contextuel n'a pas d'édition préenregistrée : il répond par
    une explication, sans jamais modifier le résultat affiché."""
    r = client.post(
        "/api/chat/contextuel",
        json={"feature": "conclusions", "resultat_actuel": {"arguments": []}, "message": "développe le premier argument"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["resultat_modifie"] is None
    assert data["operation"] == "none"
    assert "démo" in data["reponse_agent"].lower()


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


def test_config_expose_le_commit_deploye(client: TestClient, monkeypatch):
    """Sur Render, RENDER_GIT_COMMIT identifie la version en ligne (7 caractères)."""
    assert client.get("/api/config").json()["commit"] is None
    monkeypatch.setenv("RENDER_GIT_COMMIT", "06ce1c5a1b2c3d4e5f60718293a4b5c6d7e8f901")
    assert client.get("/api/config").json()["commit"] == "06ce1c5"
