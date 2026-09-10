"""
test_epingles.py — Tests de POST/GET/DELETE /api/epingles (voir
AUDIT_TASKBAR.md, étape 2 : épinglage). Fonctionne en mode démo (aucun
appel Claude nécessaire pour épingler/lister/désépingler)."""

from fastapi.testclient import TestClient


def test_epingler_un_dossier(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/epingles/", json={"type": "dossier", "reference_id": dossier_demo_id, "libelle": "Diallo c/ Atlas Logistique"})
    assert r.status_code == 201
    data = r.json()
    assert data["type"] == "dossier"
    assert data["reference_id"] == dossier_demo_id

    liste = client.get("/api/epingles/").json()
    assert any(e["id"] == data["id"] for e in liste)


def test_epingler_un_dossier_inconnu_404(client: TestClient):
    r = client.post("/api/epingles/", json={"type": "dossier", "reference_id": 999999, "libelle": "Fantôme"})
    assert r.status_code == 404


def test_epingler_deux_fois_le_meme_element_est_idempotent(client: TestClient, dossier_demo_id: int):
    """Épingler un élément déjà épinglé ne doit jamais créer un doublon --
    retourne le pin existant."""
    r1 = client.post("/api/epingles/", json={"type": "dossier", "reference_id": dossier_demo_id, "libelle": "Diallo"})
    r2 = client.post("/api/epingles/", json={"type": "dossier", "reference_id": dossier_demo_id, "libelle": "Diallo (relibellé)"})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]
    liste = [e for e in client.get("/api/epingles/").json() if e["reference_id"] == dossier_demo_id]
    assert len(liste) == 1


def test_desepingler_ne_supprime_jamais_le_dossier(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/epingles/", json={"type": "dossier", "reference_id": dossier_demo_id, "libelle": "Diallo"})
    pin_id = r.json()["id"]

    r_del = client.delete(f"/api/epingles/{pin_id}")
    assert r_del.status_code == 204

    # Le pin a disparu...
    liste = client.get("/api/epingles/").json()
    assert not any(e["id"] == pin_id for e in liste)
    # ...mais le dossier original existe toujours.
    r_dossier = client.get(f"/api/dossiers/{dossier_demo_id}")
    assert r_dossier.status_code == 200


def test_epingler_une_analyse_inexistante_404(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/epingles/", json={"type": "analyse", "reference_id": 999999, "dossier_id": dossier_demo_id, "libelle": "Analyse fantôme"}
    )
    assert r.status_code == 404


def test_epingler_une_analyse_sans_dossier_id_est_rejete(client: TestClient):
    r = client.post("/api/epingles/", json={"type": "analyse", "reference_id": 1, "libelle": "Sans dossier"})
    assert r.status_code == 422


def test_supprimer_le_dossier_supprime_ses_pins_en_cascade(client: TestClient):
    """Le sens inverse : supprimer l'original doit bien retirer le(s) pin(s)
    qui le référençaient (mais jamais l'inverse, voir le test ci-dessus)."""
    dossier = client.post("/api/dossiers/", json={"nom": "Dossier temporaire à épingler"}).json()
    pin = client.post("/api/epingles/", json={"type": "dossier", "reference_id": dossier["id"], "libelle": dossier["nom"]}).json()

    client.delete(f"/api/dossiers/{dossier['id']}")

    liste = client.get("/api/epingles/").json()
    assert not any(e["id"] == pin["id"] for e in liste)
