"""
test_corpus_fichier.py — Tests de POST /api/jurisprudence/corpus/importer-fichier
(voir AUDIT_IMPORT_EXPORT.md) : import d'un texte de corpus juridique à
partir d'un fichier plutôt que d'un texte collé. Réutilise
app.deps.extraire_texte_upload, déjà couvert en détail par
test_import_sans_dossier.py -- ces tests portent sur le comportement propre
à cet endpoint (métadonnées, insertion en base, référence par défaut), pas
sur l'extraction elle-même.

Fonctionne entièrement en mode démo (actif dans toute la suite, voir
conftest.py) : l'extraction PDF n'appelle jamais Claude.
"""

import io

from fastapi.testclient import TestClient


def _pdf_bytes(texte: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = 750
    for ligne in texte.split("\n"):
        c.drawString(100, y, ligne)
        y -= 20
    c.showPage()
    c.save()
    return buffer.getvalue()


def test_import_fichier_corpus_cree_un_texte_en_attente(client: TestClient):
    contenu = _pdf_bytes("Acte uniforme portant sur le droit commercial général.")
    r = client.post(
        "/api/jurisprudence/corpus/importer-fichier",
        files={"fichier": ("acte_ohada.pdf", contenu, "application/pdf")},
        data={"source": "OHADA", "pays": "", "type_texte": "Acte uniforme", "domaine": "Droit commercial", "reference": "", "date_texte": ""},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["source"] == "OHADA"
    assert data["validee"] == 0
    assert "commercial" in data["contenu"].lower()
    # Reste effectivement en attente (visible via /corpus/en-attente), jamais
    # validé automatiquement par un simple import de fichier.
    en_attente = client.get("/api/jurisprudence/corpus/en-attente").json()
    assert any(t["id"] == data["id"] for t in en_attente)


def test_reference_par_defaut_est_le_nom_du_fichier(client: TestClient):
    contenu = _pdf_bytes("Texte sans référence explicite fournie par l'utilisateur.")
    r = client.post(
        "/api/jurisprudence/corpus/importer-fichier",
        files={"fichier": ("traite_cedeao.pdf", contenu, "application/pdf")},
        data={"source": "CEDEAO", "pays": "", "type_texte": "", "domaine": "", "reference": "", "date_texte": ""},
    )
    assert r.status_code == 201
    assert r.json()["reference"] == "traite_cedeao.pdf"


def test_reference_fournie_prevaut_sur_le_nom_du_fichier(client: TestClient):
    contenu = _pdf_bytes("Un autre texte juridique.")
    r = client.post(
        "/api/jurisprudence/corpus/importer-fichier",
        files={"fichier": ("brut.pdf", contenu, "application/pdf")},
        data={"source": "CEDEAO", "pays": "", "type_texte": "", "domaine": "", "reference": "Traité révisé, art. 3", "date_texte": ""},
    )
    assert r.status_code == 201
    assert r.json()["reference"] == "Traité révisé, art. 3"


def test_source_manquante_est_rejetee(client: TestClient):
    contenu = _pdf_bytes("Peu importe le contenu.")
    r = client.post(
        "/api/jurisprudence/corpus/importer-fichier",
        files={"fichier": ("sans_source.pdf", contenu, "application/pdf")},
        data={"pays": "", "type_texte": "", "domaine": "", "reference": "", "date_texte": ""},
    )
    assert r.status_code == 422  # champ requis manquant (validation FastAPI, pas notre code)


def test_pdf_scanne_renvoie_422_explicite(client: TestClient):
    """Même garde-fou que pour l'import de dossier -- un PDF sans texte
    exploitable n'est pas silencieusement inséré comme corpus vide."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.showPage()  # page blanche -- pas de texte exploitable
    c.save()
    contenu = buffer.getvalue()

    r = client.post(
        "/api/jurisprudence/corpus/importer-fichier",
        files={"fichier": ("scan.pdf", contenu, "application/pdf")},
        data={"source": "OHADA", "pays": "", "type_texte": "", "domaine": "", "reference": "", "date_texte": ""},
    )
    assert r.status_code == 422
    assert "numérisé" in r.json()["detail"].lower()
