"""
extract.py — Extraction de texte depuis un fichier PDF, DOCX, XLSX, TXT
ou image (PNG/JPG/WEBP, via la vision de Claude pour la transcription).
"""

import base64
from pathlib import Path

FORMATS_SUPPORTES = ".pdf, .docx, .xlsx, .xls, .txt, .png, .jpg, .jpeg, .webp"


def extract_text(file_path: str) -> str:
    """Extrait le texte d'un fichier, quel que soit son format parmi ceux supportés."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(path)
    elif suffix == ".docx":
        return _extract_docx(path)
    elif suffix in (".xlsx", ".xls"):
        return _extract_xlsx(path)
    elif suffix == ".txt":
        return _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    elif suffix in (".png", ".jpg", ".jpeg", ".webp"):
        return _extract_image(path)
    else:
        raise ValueError(f"Format non supporté : {suffix} (formats acceptés : {FORMATS_SUPPORTES})")


def _extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber n'est pas installé. Lancez : pip install pdfplumber --break-system-packages"
        )
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return _clean_text("\n".join(text_parts))


def _extract_docx(path: Path) -> str:
    try:
        import docx
    except ImportError:
        raise ImportError(
            "python-docx n'est pas installé. Lancez : pip install python-docx --break-system-packages"
        )
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return _clean_text("\n".join(paragraphs))


def _extract_xlsx(path: Path) -> str:
    """Extrait le contenu d'un fichier Excel sous forme de texte tabulaire
    lisible, feuille par feuille — utile pour des tableaux de préjudice,
    de factures, de calculs d'indemnités, etc."""
    try:
        import openpyxl
    except ImportError:
        raise ImportError(
            "openpyxl n'est pas installé. Lancez : pip install openpyxl --break-system-packages"
        )
    wb = openpyxl.load_workbook(path, data_only=True)
    parts = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        lignes_feuille = []
        for row in ws.iter_rows(values_only=True):
            if any(cell is not None and str(cell).strip() for cell in row):
                ligne = " | ".join(str(cell).strip() if cell is not None else "" for cell in row)
                lignes_feuille.append(ligne)
        if lignes_feuille:
            parts.append(f"--- Feuille : {sheet_name} ---")
            parts.extend(lignes_feuille)
    return _clean_text("\n".join(parts))


def _extract_image(path: Path) -> str:
    """Transcrit le contenu d'une image (photo de document, capture
    d'écran...) en texte, via la vision de Claude. Nécessite une clé API
    valide (apikey.txt ou ANTHROPIC_API_KEY), la même que pour le reste
    de l'agent."""
    from analyse import _client

    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    suffix = path.suffix.lower()
    media_type = media_types.get(suffix)
    if not media_type:
        raise ValueError(f"Format d'image non supporté : {suffix}")

    data_b64 = base64.standard_b64encode(path.read_bytes()).decode("utf-8")

    client = _client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data_b64}},
                {"type": "text", "text": (
                    "Transcris intégralement et fidèlement tout le texte visible dans cette "
                    "image (document juridique, courrier, formulaire...), en respectant autant "
                    "que possible la mise en page d'origine. Si l'image contient des éléments "
                    "non textuels pertinents (tableau, schéma, signature, cachet), décris-les "
                    "brièvement aussi. Ne commente pas, ne résume pas — transcris le contenu réel."
                )},
            ],
        }],
    )
    return response.content[0].text.strip()


def _clean_text(text: str) -> str:
    """Nettoyage basique : lignes vides multiples, espaces superflus."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
