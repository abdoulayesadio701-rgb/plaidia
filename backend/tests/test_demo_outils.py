"""Réponses du mode démo pour les fonctions qui renvoyaient une 503
(app/demo_data_outils.py) : chacune répond 200 au format de son schéma, et les
résultats liés à un dossier sont persistés comme de vrais résultats."""

import pytest
from fastapi.testclient import TestClient

TEXTE = "Le 12 mars 2024, M. Karim Diallo a assigné la SAS Atlas Logistique devant le tribunal."


def test_traduction_detecte_la_langue_et_repond(client: TestClient):
    fr = client.post("/api/analyse/traduire", json={"texte": "Le salarié conteste son licenciement pour faute grave."}).json()
    assert fr["langue_detectee"] == "Français" and fr["langue_cible"] == "English" and fr["texte_traduit"]
    en = client.post("/api/analyse/traduire", json={"texte": "The employee was dismissed and his claim is that the notice was late."}).json()
    assert en["langue_detectee"] == "English" and en["langue_cible"] == "Français"


def test_classement_repere_la_nature(client: TestClient):
    assert client.post("/api/greffier/classement", json={"texte": "ASSIGNATION devant le tribunal"}).json()["nature"] == "assignation"
    assert client.post("/api/greffier/classement", json={"texte": "PAR CES MOTIFS le tribunal"}).json()["nature"] == "jugement"
    inconnu = client.post("/api/greffier/classement", json={"texte": "Bonjour tout le monde"}).json()
    assert inconnu["nature"] == "autre" and inconnu["confiance"] == "Faible"


def test_coherence_compare_les_dates_des_documents(client: TestClient):
    r = client.post("/api/greffier/coherence", json={"documents": [
        {"nom_document": "Contrat", "texte": "Signé le 12 mars 2024."},
        {"nom_document": "Lettre", "texte": "Signé le 15 mars 2024 et rappelé le 12 mars 2024."},
    ]})
    assert r.status_code == 200
    data = r.json()
    assert set(data["elements_par_document"]) == {"Contrat", "Lettre"}
    assert data["elements_par_document"]["Lettre"]["dates"] == ["15 mars 2024", "12 mars 2024"]
    assert len(data["contradictions"]) == 1 and "15 mars 2024" in data["contradictions"][0]["document_2"]
    assert data["elements_coherents"] == ["Date présente dans les deux documents : 12 mars 2024"]
    assert data["limites_analyse"]


def test_pv_audience_reprend_les_notes(client: TestClient):
    r = client.post("/api/greffier/pv-audience", json={"notes": "- Ouverture à 14h\n- Témoin entendu"})
    assert r.status_code == 200
    assert "Ouverture à 14h" in r.json()["texte"] and "Témoin entendu" in r.json()["texte"]


def test_requisitoire_et_rapport_instruction(client: TestClient):
    r1 = client.post("/api/greffier/requisitoire", json={"texte": TEXTE})
    assert r1.status_code == 200 and r1.json()["qualification_retenue"] and r1.json()["peine_requise"]
    r2 = client.post("/api/greffier/rapport-instruction", json={"texte": TEXTE})
    assert r2.status_code == 200 and r2.json()["actes_instruction"] and r2.json()["sens_propose"]


def test_prise_de_note_structuree_et_enregistree(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/notes/", json={"dossier_id": dossier_demo_id, "note_brute": "Penser à relancer le client. Vérifier la pièce 4."})
    assert r.status_code == 201
    note = r.json()
    assert "Note structurée" in note["note_structuree"]
    assert note["actions"] and note["points"]
    assert any(n["id"] == note["id"] for n in client.get(f"/api/notes/dossier/{dossier_demo_id}").json())


def test_note_client_persistee_et_relue(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/notes/note-client", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    corps = r.json()
    assert "Madame, Monsieur" in corps["texte"] and corps["document_id"] is not None
    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "note_client"}).json()
    assert liste[0]["id"] == corps["document_id"]


def test_verification_procedurale_persistee_et_relue(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/greffier/verification-procedurale", json={"dossier_id": dossier_demo_id})
    assert r.status_code == 200
    corps = r.json()
    assert corps["echeances_identifiees"] and corps["actes_potentiellement_manquants"] and corps["points_attention"]
    assert corps["document_id"] is not None
    assert {e["statut"] for e in corps["echeances_identifiees"]} <= {"À venir", "Proche", "Possiblement dépassée", "Date incertaine"}


def test_consultation_jurisprudence_persistee(client: TestClient, dossier_demo_id: int):
    r = client.post("/api/jurisprudence/consulter", json={"dossier_id": dossier_demo_id, "question": "Retards liés à une grève : faute grave ?"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["notions"]["domaine"] and corps["reponse"] and corps["document_id"] is not None
    liste = client.get(f"/api/dossiers/{dossier_demo_id}/documents-generes", params={"feature": "jurisprudence_consultation"}).json()
    assert liste and liste[0]["id"] == corps["document_id"]


def test_consultation_dossier_inconnu_404_en_mode_demo(client: TestClient):
    r = client.post("/api/jurisprudence/consulter", json={"dossier_id": 999999, "question": "x"})
    assert r.status_code == 404


@pytest.mark.parametrize("chemin,cle", [
    ("/api/analyse/style", "texte"),
    ("/api/analyse/traduire", "texte"),
    ("/api/greffier/extraction", "texte"),
    ("/api/greffier/classement", "texte"),
    ("/api/greffier/pv-audience", "notes"),
    ("/api/greffier/requisitoire", "texte"),
    ("/api/greffier/rapport-instruction", "texte"),
])
def test_texte_vide_reste_rejete(client: TestClient, chemin: str, cle: str):
    """Le mode démo ne contourne pas la validation d'entrée."""
    assert client.post(chemin, json={cle: ""}).status_code == 422


def test_reponses_en_anglais_avec_l_interface_en_anglais(client: TestClient, dossier_demo_id: int):
    en = {"x-langue": "en"}
    assert "Dear Sir or Madam" in client.post("/api/notes/note-client", json={"dossier_id": dossier_demo_id}, headers=en).json()["texte"]
    r = client.post("/api/greffier/requisitoire", json={"texte": TEXTE}, headers=en)
    assert "fictional" in r.json()["qualification_retenue"].lower()
    assert "Demo mode" in client.post(
        "/api/chat/contextuel", json={"feature": "plan", "resultat_actuel": {}, "message": "x"}, headers=en
    ).json()["reponse_agent"]


def test_collecte_de_jurisprudence_en_demo_sans_doublon_ni_appel_reseau(client: TestClient, monkeypatch):
    import judilibre

    def interdit(*a, **k):
        raise AssertionError("le mode démo ne doit jamais appeler Judilibre")

    monkeypatch.setattr(judilibre, "collecter_jurisprudence", interdit)
    for _ in range(2):
        r = client.post("/api/jurisprudence/collecter", json={"query": "faute grave", "domaine": "travail"})
        assert r.status_code == 200
        assert r.json()["nombre_collecte"] == 3
        assert all("fictive" in d["reference"] for d in r.json()["decisions"])
    en_attente = client.get("/api/jurisprudence/en-attente").json()
    assert len(en_attente) == 3  # pas de doublon après deux collectes
    assert {j["domaine"] for j in en_attente} == {"travail"}


@pytest.mark.parametrize("texte,action", [
    ("rédiger une note client", "note_client"),
    ("consulter les notes", "notes_consulter"),
    ("prendre une note", "note"),
    ("vérifier la procédure", "verification"),
    ("calculer les délais d'appel", "delais"),
    ("je veux m'entraîner à plaider", "entrainement"),
    ("montre le bordereau de pièces", "bordereau"),
    ("construire la chronologie", "chronologie"),
    ("simuler les objections", "simulateur"),
    ("générer le rapport complet", "rapport"),
    ("résume le dossier", "resumer"),
    ("importer des documents", "importer"),
])
def test_intention_demo_reconnait_chaque_action(client: TestClient, texte: str, action: str):
    assert client.post("/api/intention/interpreter", json={"texte": texte}).json()["action"] == action


def test_intention_demo_duree_et_langue(client: TestClient):
    r = client.post("/api/intention/interpreter", json={"texte": "make a plea plan of 25 minutes"}, headers={"x-langue": "en"}).json()
    assert r["action"] == "plan" and r["duree_minutes"] == 25 and r["reformulation"].startswith("Understood")
    # la durée n'est extraite que pour le plan et l'entraînement
    assert client.post("/api/intention/interpreter", json={"texte": "résume le dossier en 5 minutes"}).json()["duree_minutes"] is None


def test_toutes_les_actions_demo_sont_declarees_dans_le_prompt_reel():
    """Une action inventée côté démo n'aurait aucune route côté front."""
    import analyse as legacy_analyse
    from app import demo_data_outils

    for action, _ in demo_data_outils._INTENTIONS:
        assert f'- "{action}" :' in legacy_analyse.INTENTION_SYSTEM_PROMPT, action
