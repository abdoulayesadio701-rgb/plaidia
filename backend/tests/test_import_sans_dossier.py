"""
test_import_sans_dossier.py — Tests de POST /api/dossiers/extraire, l'import
de fichier SANS rattachement à un dossier (voir
ARCHITECTURE_CHAT_CONTEXTUEL.md §2.6, phases 6-8), utilisé par PvAudiencePage
et CoherencePage, volontairement indépendantes de tout dossier.

Fonctionne entièrement en mode démo (actif dans toute la suite, voir
conftest.py) : l'extraction PDF/DOCX/XLSX/TXT n'appelle jamais Claude --
seule la transcription d'image en a besoin, hors périmètre de ces tests.
"""

import io

from fastapi.testclient import TestClient


def _pdf_bytes(texte_par_page: list[str]) -> bytes:
    """Génère un vrai PDF en mémoire via reportlab (déjà une dépendance du
    projet, utilisée par export.py)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    for texte in texte_par_page:
        if texte:
            y = 750
            for ligne in texte.split("\n"):
                c.drawString(100, y, ligne)
                y -= 20
        c.showPage()
    c.save()
    return buffer.getvalue()


def test_extraction_pdf_normal_sans_dossier(client: TestClient):
    contenu = _pdf_bytes(["Notes d'audience : le président rappelle les faits de la cause."])
    r = client.post("/api/dossiers/extraire", files={"fichier": ("audience.pdf", contenu, "application/pdf")})
    assert r.status_code == 201
    data = r.json()
    assert "audience" in data["texte_extrait"].lower() or "faits" in data["texte_extrait"].lower()
    assert data["nom_fichier"] == "audience.pdf"
    assert data["caracteres_extraits"] > 0


def test_extraction_pdf_scanne_renvoie_422_explicite(client: TestClient):
    contenu = _pdf_bytes([""])  # page blanche -- pas de texte exploitable
    r = client.post("/api/dossiers/extraire", files={"fichier": ("scan.pdf", contenu, "application/pdf")})
    assert r.status_code == 422
    assert "numérisé" in r.json()["detail"].lower()


def test_extraction_ne_touche_aucun_dossier(client: TestClient, dossier_demo_id: int):
    """N'écrit rien en base -- le texte extrait n'apparaît jamais dans les
    faits d'un dossier existant, contrairement à POST /{dossier_id}/documents."""
    faits_avant = client.get(f"/api/dossiers/{dossier_demo_id}").json()["faits"]
    contenu = _pdf_bytes(["Un texte qui ne doit atterrir dans aucun dossier."])
    r = client.post("/api/dossiers/extraire", files={"fichier": ("libre.pdf", contenu, "application/pdf")})
    assert r.status_code == 201
    faits_apres = client.get(f"/api/dossiers/{dossier_demo_id}").json()["faits"]
    assert faits_avant == faits_apres


def test_extraction_format_non_supporte_rejete(client: TestClient):
    r = client.post("/api/dossiers/extraire", files={"fichier": ("archive.zip", b"PK\x03\x04", "application/zip")})
    assert r.status_code == 415


def test_extraction_txt_simple(client: TestClient):
    r = client.post(
        "/api/dossiers/extraire",
        files={"fichier": ("notes.txt", "Texte brut sans dossier.".encode("utf-8"), "text/plain")},
    )
    assert r.status_code == 201
    assert "Texte brut" in r.json()["texte_extrait"]


def test_extraction_fichier_vide_rejetee(client: TestClient):
    r = client.post("/api/dossiers/extraire", files={"fichier": ("vide.txt", b"", "text/plain")})
    assert r.status_code == 422
    assert "vide" in r.json()["detail"].lower()


def test_extraction_pdf_corrompu_rejete_proprement(client: TestClient):
    """Une extension valide mais un contenu illisible (pas un vrai PDF) ne
    doit jamais remonter comme une 500 générique -- toujours une erreur
    explicite (voir ARCHITECTURE_CHAT_CONTEXTUEL.md §13)."""
    r = client.post("/api/dossiers/extraire", files={"fichier": ("faux.pdf", b"ceci n'est pas un PDF valide", "application/pdf")})
    assert r.status_code == 422
    assert "corrompu" in r.json()["detail"].lower() or "inattendu" in r.json()["detail"].lower()


def test_extraction_docx_corrompu_rejete_proprement(client: TestClient):
    r = client.post("/api/dossiers/extraire", files={"fichier": ("faux.docx", b"pas un vrai docx", "application/vnd.openxmlformats")})
    assert r.status_code == 422


def test_extraction_fichier_trop_volumineux_rejete(client: TestClient):
    contenu_trop_gros = b"a" * (20 * 1024 * 1024 + 1)  # 1 octet au-dessus de la limite
    r = client.post("/api/dossiers/extraire", files={"fichier": ("enorme.txt", contenu_trop_gros, "text/plain")})
    assert r.status_code == 413
    assert "volumineux" in r.json()["detail"].lower()


def test_extraction_fichier_juste_sous_la_limite_accepte(client: TestClient):
    contenu = b"a" * (1024 * 1024)  # 1 Mo, largement sous la limite
    r = client.post("/api/dossiers/extraire", files={"fichier": ("acceptable.txt", contenu, "text/plain")})
    assert r.status_code == 201


def test_import_avec_dossier_fichier_vide_rejete(client: TestClient, dossier_demo_id: int):
    """Même garde-fou sur l'endpoint historique (POST /{id}/documents),
    pas seulement sur le nouveau POST /extraire."""
    r = client.post(f"/api/dossiers/{dossier_demo_id}/documents", files={"fichier": ("vide.txt", b"", "text/plain")})
    assert r.status_code == 422
