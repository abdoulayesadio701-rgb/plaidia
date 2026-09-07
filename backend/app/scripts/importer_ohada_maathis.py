"""
importer_ohada_maathis.py — Import ponctuel du corpus OHADA structuré
publié par Maathis-com sur Hugging Face (CC-BY-4.0) dans corpus_juridique.

Source : https://huggingface.co/datasets/Maathis-com/ohada-actes-uniformes
- nodes/articles.csv : 3126 articles des 9 Actes uniformes OHADA
- nodes/actes_uniformes.csv : métadonnées des 9 actes (nom complet, date)

⚠️ Attention qualité : l'extraction automatisée du texte contient des
artefacts OCR visibles sur les caractères accentués (ex. "societe" au lieu
de "société", "Btat" au lieu de "État") -- voir la conversation qui a motivé
cet import. Le texte est importé TEL QUEL, sans correction automatique
(un remplacement aveugle risquerait de corrompre du texte correct). C'est
précisément pour cette raison que l'import laisse tout en attente
(validee=False) : voir db.py::valider_texte_corpus_par_source pour la
validation en bloc, à faire en connaissance de cause après un échantillonnage
manuel -- pas un réflexe.

Usage : depuis backend/, avec le venv actif :
    python -m app.scripts.importer_ohada_maathis
"""

import csv
import io
import sys
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR.parent))  # racine du dépôt -- pour importer db.py tel quel

import db  # noqa: E402

BASE_URL = "https://huggingface.co/datasets/Maathis-com/ohada-actes-uniformes/resolve/main"
SOURCE = "OHADA"


def _telecharger_csv(nom_fichier: str) -> list[dict]:
    resp = requests.get(f"{BASE_URL}/{nom_fichier}", timeout=60)
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def importer() -> int:
    print("Téléchargement des métadonnées des actes uniformes...")
    actes = {row["acte_id"]: row for row in _telecharger_csv("nodes/actes_uniformes.csv")}
    print(f"  {len(actes)} actes uniformes trouvés.")

    print("Téléchargement des articles (peut prendre quelques secondes, ~2 Mo)...")
    articles = _telecharger_csv("nodes/articles.csv")
    print(f"  {len(articles)} articles trouvés.")

    deja_presents = {
        t["reference"] for t in db.get_corpus_en_attente() + db.get_corpus_valide(source=SOURCE)
    }

    nb_importes = 0
    nb_ignores = 0
    for ligne in articles:
        acte_code = ligne["acte_code"]
        acte = actes.get(acte_code)
        reference = f"{acte_code} - Article {ligne['article_number']}"

        if reference in deja_presents:
            nb_ignores += 1
            continue

        db.ajouter_texte_corpus(
            source=SOURCE,
            contenu=ligne["text"],
            pays="",  # supranational -- 17 États membres, pas un seul pays
            type_texte="Acte uniforme",
            domaine=acte["full_name"] if acte else acte_code,
            reference=reference,
            date_texte=acte["adopted"] if acte else "",
            validee=False,  # jamais pré-validé -- voir avertissement en tête de fichier
        )
        nb_importes += 1

    print(f"Import terminé : {nb_importes} articles importés, {nb_ignores} déjà présents (ignorés).")
    return nb_importes


if __name__ == "__main__":
    importer()
