"""Tests de /api/generations -- lancement en arrière-plan, suivi et
suppression explicite (voir db.py, section "Générations", et
routers/generations.py). Mode démo (voir conftest.py) : rapide et
déterministe, aucun appel réseau réel."""

import time

import analyse as legacy_analyse
from app.routers.generations import _lancer_arriere_plan
from fastapi.testclient import TestClient


def _attendre_fin(client: TestClient, generation_id: int, timeout: float = 5.0) -> dict:
    """Poll GET /api/generations/{id} jusqu'à ce que statut != 'en_cours'
    -- le traitement tourne dans un vrai thread serveur, pas simulé."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        reponse = client.get(f"/api/generations/{generation_id}")
        assert reponse.status_code == 200
        donnees = reponse.json()
        if donnees["statut"] != "en_cours":
            return donnees
        time.sleep(0.05)
    raise AssertionError(f"Génération {generation_id} toujours en_cours après {timeout}s")


def test_lancement_renvoie_immediatement_un_id_en_cours(client: TestClient, dossier_demo_id: int):
    reponse = client.post("/api/generations/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 10})
    assert reponse.status_code == 202
    donnees = reponse.json()
    assert donnees["statut"] == "en_cours"
    assert isinstance(donnees["id"], int)
    # Vidange le thread avant de rendre la main : le fixture `client` du
    # test suivant réinitialise la base (mode démo, voir conftest.py) --
    # sans ça, ce thread encore actif se retrouverait à écrire dans des
    # tables droppées entre-temps (uniquement un artefact de cette suite
    # de tests, pas un souci du code de production lui-même).
    _attendre_fin(client, donnees["id"])


def test_plan_en_arriere_plan_se_termine_et_est_persiste(client: TestClient, dossier_demo_id: int):
    lancement = client.post("/api/generations/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 10})
    generation = _attendre_fin(client, lancement.json()["id"])

    assert generation["statut"] == "terminee"
    assert generation["type"] == "plan"
    assert generation["dossier_id"] == dossier_demo_id
    assert generation["contenu"]["document_id"] is not None

    # Persisté aussi dans documents_generes (comme la variante synchrone) --
    # les deux tables coexistent, l'historique générique ne remplace pas
    # le document éditorial existant.
    liste_documents = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes").json()
    assert any(d["feature"] == "plan" for d in liste_documents)


def test_conclusions_sans_dossier_fonctionne_en_arriere_plan(client: TestClient):
    """besoin_dossier=False côté gui.py -- même chose ici : dossier_id
    optionnel, la génération n'est liée à aucun dossier."""
    lancement = client.post("/api/generations/conclusions", json={"texte": "Texte de conclusions adverses à analyser."})
    assert lancement.status_code == 202
    generation = _attendre_fin(client, lancement.json()["id"])
    assert generation["statut"] == "terminee"
    assert generation["dossier_id"] is None
    assert generation["contenu"]["analyse_id"] is None


def test_liste_et_filtre_par_dossier(client: TestClient, dossier_demo_id: int):
    lancement = client.post("/api/generations/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 5})
    _attendre_fin(client, lancement.json()["id"])

    toutes = client.get("/api/generations/").json()
    assert any(g["id"] == lancement.json()["id"] for g in toutes)

    filtrees = client.get("/api/generations/", params={"dossier_id": dossier_demo_id}).json()
    assert all(g["dossier_id"] == dossier_demo_id for g in filtrees)


def test_generation_introuvable_renvoie_404(client: TestClient):
    assert client.get("/api/generations/999999").status_code == 404


def test_suppression_est_definitive(client: TestClient, dossier_demo_id: int):
    lancement = client.post("/api/generations/plan", json={"dossier_id": dossier_demo_id, "temps_minutes": 5})
    generation_id = lancement.json()["id"]
    _attendre_fin(client, generation_id)

    suppression = client.delete(f"/api/generations/{generation_id}")
    assert suppression.status_code == 204
    assert client.get(f"/api/generations/{generation_id}").status_code == 404


def test_suppression_du_dossier_ne_supprime_pas_lhistorique(client: TestClient):
    """FOREIGN KEY dossier_id ... ON DELETE SET NULL (pas CASCADE) --
    voir db.py. Créé et détruit son propre dossier pour ne pas perturber
    dossier_demo_id, réutilisé par les autres tests."""
    nouveau = client.post("/api/dossiers/", json={"nom": "Dossier temporaire pour suppression"}).json()
    lancement = client.post("/api/generations/plan", json={"dossier_id": nouveau["id"], "temps_minutes": 5})
    generation = _attendre_fin(client, lancement.json()["id"])

    assert client.delete(f"/api/dossiers/{nouveau['id']}").status_code == 204

    apres = client.get(f"/api/generations/{generation['id']}")
    assert apres.status_code == 200
    assert apres.json()["dossier_id"] is None


def test_cle_api_et_langue_survivent_au_reset_du_contextvar_par_le_middleware(client: TestClient):
    """Le vrai risque de ce mécanisme : main.py réinitialise ses ContextVars
    (clé API personnelle, langue) dans un `finally` qui s'exécute dès que
    la route renvoie sa réponse 202 -- AVANT que le thread d'arrière-plan
    n'ait fini. _lancer_arriere_plan doit donc capturer ces valeurs sur le
    thread de la requête et les reposer explicitement au début du thread,
    sinon elles reviendraient silencieusement à leurs valeurs par défaut
    (aucune clé, langue "fr") pour toute la durée du traitement."""
    vues_dans_le_thread = {}

    def tache_espion():
        vues_dans_le_thread["cle"] = legacy_analyse.obtenir_cle_api_requete()
        vues_dans_le_thread["langue"] = legacy_analyse.langue_requete()
        return {}

    jeton_cle = legacy_analyse.definir_cle_api_requete("sk-ant-test-personnelle")
    jeton_langue = legacy_analyse.definir_langue_requete("en")
    try:
        generation_id = _lancer_arriere_plan("test", None, "Test propagation contexte", tache_espion)
    finally:
        # Simule EXACTEMENT le `finally` des middlewares de main.py, qui
        # s'exécute dès que la route a renvoyé sa réponse -- sans attendre
        # la fin du thread lancé ci-dessus.
        legacy_analyse.reinitialiser_cle_api_requete(jeton_cle)
        legacy_analyse.reinitialiser_langue_requete(jeton_langue)

    _attendre_fin(client, generation_id)
    assert vues_dans_le_thread["cle"] == "sk-ant-test-personnelle"
    assert vues_dans_le_thread["langue"] == "en"
