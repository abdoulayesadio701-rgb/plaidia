"""
importer_corpus_ohada.py — Importe un premier lot de textes OHADA officiels
dans le corpus multi-source de Plaid'IA (table corpus_juridique), article
par article plutôt qu'en un seul bloc — pour que chaque article reste
pleinement exploitable en recherche (le contexte envoyé au modèle tronque
chaque entrée à 2000 caractères ; un article isolé y tient toujours en
entier, alors qu'un texte de loi complet serait coupé après quelques
articles seulement).

Source : Journal Officiel de l'OHADA, republié par le Ministère de la
Justice du Sénégal (https://justice.sec.gouv.sn) — textes officiels, accès
libre, sans connexion requise.

Usage :
    Placez ce script et le dossier "textes/" à côté de db.py, puis lancez :
        python importer_corpus_ohada.py

    Chaque article est importé PRÉ-VALIDÉ (validee=True) puisqu'il provient
    d'une source officielle directement vérifiable — contrairement à la
    jurisprudence collectée via Judilibre, qui reste à valider manuellement
    par l'avocat.
"""

import re
from pathlib import Path

import db

DOSSIER_TEXTES = Path(__file__).parent / "textes"


def decouper_en_articles(texte: str) -> list[tuple[str, str]]:
    """Découpe un Acte uniforme en articles individuels à partir des
    marqueurs 'ARTICLE N-'. Retourne une liste de (numero, contenu)."""
    morceaux = re.split(r'\n(ARTICLE \d+-)', texte)
    articles = []
    for i in range(1, len(morceaux), 2):
        marqueur = morceaux[i]
        contenu = morceaux[i + 1] if i + 1 < len(morceaux) else ""
        numero = re.search(r'\d+', marqueur).group()
        contenu = contenu.strip()
        if contenu:
            articles.append((numero, contenu))
    return articles


# Chaque entrée décrit un Acte uniforme à importer : le nom du fichier texte
# (dans le dossier "textes/"), sa référence officielle complète, et son
# domaine pour faciliter le tri ultérieur.
TEXTES_A_IMPORTER = [
    {
        "fichier": "AUDCG.txt",
        "reference_base": "Acte uniforme portant sur le Droit Commercial Général (AUDCG), adopté le 15 décembre 2010 à Lomé",
        "domaine": "Droit commercial général",
    },
    {
        "fichier": "AUS.txt",
        "reference_base": "Acte uniforme portant Organisation des Sûretés (AUS), adopté le 15 décembre 2010 à Lomé",
        "domaine": "Sûretés (cautionnement, gage, nantissement, hypothèque)",
    },
    # Ajoutez ici d'autres Actes uniformes au même format, par exemple :
    # {
    #     "fichier": "AUSCGIE.txt",
    #     "reference_base": "Acte uniforme relatif au droit des sociétés commerciales et du GIE, adopté le 30 janvier 2014 à Ouagadougou",
    #     "domaine": "Droit des sociétés commerciales",
    # },
]


def importer_texte(fichier: str, reference_base: str, domaine: str) -> int:
    chemin = DOSSIER_TEXTES / fichier
    if not chemin.exists():
        print(f"  ⚠ Fichier introuvable, ignoré : {chemin}")
        return 0

    texte = chemin.read_text(encoding="utf-8")
    articles = decouper_en_articles(texte)

    compte = 0
    for numero, contenu in articles:
        db.ajouter_texte_corpus(
            source="OHADA",
            contenu=contenu,
            pays="Espace OHADA (17 États membres)",
            type_texte="Acte uniforme",
            domaine=domaine,
            reference=f"{reference_base} — Article {numero}",
            date_texte="",
            validee=True,  # Source officielle directement vérifiable
        )
        compte += 1
    return compte


def main():
    db.init_db()
    print("Import du corpus OHADA en cours...\n")
    total = 0
    for item in TEXTES_A_IMPORTER:
        print(f"→ {item['fichier']} ({item['domaine']})")
        n = importer_texte(item["fichier"], item["reference_base"], item["domaine"])
        print(f"  {n} article(s) importé(s), pré-validés.")
        total += n
    print(f"\n✅ Import terminé : {total} article(s) OHADA au total dans le corpus.")
    print("Ils sont immédiatement utilisables dans Le Grimoire → Consulter la jurisprudence,")
    print("en choisissant « OHADA » dans le sélecteur « ⚖ Droit » en haut de l'écran.")


if __name__ == "__main__":
    main()
