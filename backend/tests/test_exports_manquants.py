"""
test_exports_manquants.py — Tests des 3 exports ajoutés lors de l'audit
import/export (AUDIT_IMPORT_EXPORT.md §B) : simulateur d'objections,
chronologie, vérification procédurale -- les seules fonctionnalités de
l'Arsenal/Greffier qui produisaient un résultat structuré sans jamais
pouvoir l'exporter. La chronologie était initialement exportée en CSV,
repassée en Word pour ne garder que Word/PDF comme formats d'export dans
toute l'application.

Fonctionne en mode démo (voir conftest.py) : ces endpoints ne font aucun
appel Claude, seulement de la mise en forme + export.py.
"""

from fastapi.testclient import TestClient


def test_export_simulateur_word(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/analyse/simulateur/export",
        json={
            "dossier_id": dossier_demo_id,
            "objections": [
                {"origine": "Juge", "question": "Pourquoi ce délai ?", "piege": "Teste la rigueur procédurale", "piste_reponse": "Rappeler l'art. X"}
            ],
            "point_le_plus_faible": "L'absence de mise en demeure préalable.",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r.content) > 0


def test_export_simulateur_dossier_inconnu_404(client: TestClient):
    r = client.post("/api/analyse/simulateur/export", json={"dossier_id": 999999, "objections": []})
    assert r.status_code == 404


def test_export_chronologie_word(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/greffier/chronologie/export",
        json={"dossier_id": dossier_demo_id, "evenements": [{"date": "12/03/2024", "evenement": "Assignation délivrée"}]},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r.content) > 0


def test_export_verification_procedurale_word(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/greffier/verification-procedurale/export",
        json={
            "dossier_id": dossier_demo_id,
            "echeances_identifiees": [{"echeance": "Conclusions à déposer", "date": "01/06/2024", "statut": "À venir"}],
            "actes_potentiellement_manquants": ["Signification du jugement"],
            "points_attention": [],
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r.content) > 0


def _texte_docx(contenu: bytes) -> str:
    import io

    from docx import Document

    return "\n".join(p.text for p in Document(io.BytesIO(contenu)).paragraphs)


def test_export_requisitoire_word(client: TestClient):
    r = client.post(
        "/api/greffier/requisitoire/export",
        json={
            "qualification_retenue": "Vol aggravé",
            "faits_et_elements_invoques": ["Effraction constatée"],
            "circonstances_aggravantes": ["Récidive"],
            "circonstances_attenuantes": [],
            "peine_requise": "2 ans dont 1 avec sursis",
            "points_attention": ["Qualification à vérifier"],
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    texte = _texte_docx(r.content)
    assert "Vol aggravé" in texte
    assert "2 ans dont 1 avec sursis" in texte
    assert "- Récidive" in texte
    assert "— Rien détecté" in texte  # circonstances atténuantes vides


def test_export_rapport_instruction_word(client: TestClient):
    r = client.post(
        "/api/greffier/rapport-instruction/export",
        json={
            "actes_instruction": ["Audition du témoin X"],
            "elements_a_charge": ["Empreintes relevées"],
            "elements_a_decharge": ["Alibi allégué"],
            "mesures_ordonnees": ["Expertise ADN"],
            "sens_propose": "Renvoi devant le tribunal correctionnel",
            "points_attention": [],
        },
    )
    assert r.status_code == 200
    texte = _texte_docx(r.content)
    assert "Renvoi devant le tribunal correctionnel" in texte
    assert "- Empreintes relevées" in texte
    assert "- Alibi allégué" in texte
    assert "- Expertise ADN" in texte


def test_export_requisitoire_corps_vide_valeurs_par_defaut(client: TestClient):
    r = client.post("/api/greffier/requisitoire/export", json={})
    assert r.status_code == 200
    assert "non précisée" in _texte_docx(r.content)


def test_export_resume_word(client: TestClient, dossier_demo_id: int):
    r = client.post(
        "/api/analyse/resume/export",
        json={
            "dossier_id": dossier_demo_id,
            "resume_court": "M. Diallo conteste son licenciement.",
            "points_cles": ["Cinq ans d'ancienneté"],
            "elements_manquants": ["Règlement intérieur"],
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    texte = _texte_docx(r.content)
    assert "M. Diallo conteste son licenciement." in texte
    assert "- Cinq ans d'ancienneté" in texte
    assert "- Règlement intérieur" in texte


def test_export_resume_dossier_inconnu_404(client: TestClient):
    assert client.post("/api/analyse/resume/export", json={"dossier_id": 999999}).status_code == 404


def test_export_conclusions_word_et_pdf(client: TestClient, dossier_demo_id: int):
    corps = {
        "dossier_id": dossier_demo_id,
        "arguments": [{"resume": "Argument adverse", "fondement": "Pièce 4", "risque": "Moyen", "justification_risque": "x", "refutations": []}],
        "points_attention": ["Vérifier le délai"],
    }
    word = client.post("/api/analyse/conclusions/export", json=corps)
    assert word.status_code == 200
    assert word.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    pdf = client.post("/api/analyse/conclusions/export", params={"format": "pdf"}, json=corps)
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
