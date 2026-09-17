"""
veille_lois.py — Veille des modifications d'articles de loi référencés dans
les dossiers actifs (France, via Légifrance). Construit en parallèle du
système de veille jurisprudence existant (voir gui.py::
_lancer_verification_veille), avec la même mécanique de "déjà vu" (table
partagée db.elements_veille_vus) -- mais un module et un thread séparés,
pour ne jamais toucher au fonctionnement de la veille jurisprudence.

Portée volontairement limitée aux 6 codes balisables par l'IA (voir
analyse.REGLE_BALISAGE_CITATIONS : CP, CCIV, CPC, CPP, CTRAV, CCOM). Le
corpus OHADA (Actes uniformes, importés manuellement depuis des .txt, voir
importer_corpus_ohada.py) n'a ni API publique ni format de balise [ART:...]
dédié -- aucune détection automatique n'y est possible avec les moyens du
bord actuels. Voir rappel_veille_ohada() pour le seul mécanisme possible :
un rappel périodique, global, non lié à un dossier précis.

Ce module ne modifie JAMAIS le contenu d'une analyse, d'un plan ou d'un
dossier existant : il détecte, journalise (db.creer_alerte_article) et
notifie, un point c'est tout. Toute vérification du fond reste manuelle.
"""

import re

import db
import legifrance

# Même regex que gui.py::_RE_TAG_ART (voir analyse.REGLE_BALISAGE_CITATIONS)
# -- dupliquée ici plutôt qu'importée de gui.py, qui n'est pas un module de
# bibliothèque (c'est le point d'entrée de l'appli elle-même).
_RE_TAG_ART = re.compile(r"\[ART:([^:\]]+):([A-Z]+)\]")

CODES_CONNUS = {"CP", "CCIV", "CPC", "CPP", "CTRAV", "CCOM"}
_CODES_LIBELLES = {
    "CP": "Code pénal", "CCIV": "Code civil", "CPC": "Code de procédure civile",
    "CPP": "Code de procédure pénale", "CTRAV": "Code du travail", "CCOM": "Code de commerce",
}

# Un article déjà vérifié il y a moins de ce délai n'est pas réinterrogé --
# Légifrance/PISTE applique un quota d'appels par jour (voir légifrance.py) ;
# vérifier chaque article une fois par jour au plus suffit largement pour
# une modification de loi, qui n'est jamais un événement à la minute près.
DELAI_MIN_ENTRE_VERIFICATIONS_HEURES = 20


def extraire_articles_cites(*textes: str) -> set[tuple[str, str]]:
    """Extrait l'ensemble des (code, numéro) référencés dans un ou
    plusieurs textes, via les balises [ART:<numéro>:<code>]. Ignore
    silencieusement tout code hors de CODES_CONNUS (balisage malformé ou
    futur code non encore supporté par la veille)."""
    trouves = set()
    for texte in textes:
        if not texte:
            continue
        for m in _RE_TAG_ART.finditer(texte):
            numero, code = m.group(1), m.group(2)
            if code in CODES_CONNUS:
                trouves.add((code, numero))
    return trouves


def _heures_depuis(iso_str: str) -> float:
    from datetime import datetime
    return (datetime.now() - datetime.fromisoformat(iso_str)).total_seconds() / 3600


def verifier_et_detecter_changement(code: str, numero: str) -> dict | None:
    """Vérifie un article auprès de Légifrance et compare au dernier état
    connu (db.articles_surveilles). Ne réinterroge pas si la dernière
    vérification date de moins de DELAI_MIN_ENTRE_VERIFICATIONS_HEURES.

    Retourne un dict de changement {"ancien_etat", "nouvel_etat",
    "date_modification", "lien"} si un changement réel a été détecté,
    None sinon (pas de changement, article non retrouvé, ou vérification
    trop récente pour être relancée) -- mais met TOUJOURS à jour le cache
    (articles_surveilles) quand une vérification a effectivement eu lieu,
    y compris la toute première fois (rien à comparer, donc jamais
    d'alerte sur la première observation d'un article)."""
    cache = db.get_article_surveille(code, numero)
    if cache is not None and _heures_depuis(cache["derniere_verification"]) < DELAI_MIN_ENTRE_VERIFICATIONS_HEURES:
        return None

    etat_actuel = legifrance.verifier_article_a_jour(_CODES_LIBELLES.get(code, code), numero)
    if etat_actuel is None:
        return None  # article non retrouvé avec certitude -- on ne se prononce pas

    changement = None
    if cache is not None:
        id_a_change = cache["dernier_id_version"] and cache["dernier_id_version"] != etat_actuel["id_version"]
        etat_a_change = cache["dernier_etat"] and cache["dernier_etat"] != etat_actuel["etat"]
        if id_a_change or etat_a_change:
            changement = {
                "ancien_etat": cache["dernier_etat"],
                "nouvel_etat": etat_actuel["etat"],
                "date_modification": etat_actuel.get("dateDebut"),
                "lien": etat_actuel["lien"],
            }

    db.upsert_article_surveille(code, numero, etat_actuel["id_version"], etat_actuel["etat"])
    return changement


def rappel_veille_ohada(seuil_mois: int = 6) -> str | None:
    """Seul mécanisme possible côté OHADA (voir docstring du module) : un
    rappel textuel si le corpus n'a pas été revérifié manuellement depuis
    `seuil_mois` mois, sans distinction de dossier (impossible à établir
    sans balisage dédié). Retourne le texte du rappel, ou None si la
    dernière vérification est encore récente ou si elle n'a jamais été
    posée (première utilisation -- pas de rappel avant une première
    vérification de référence)."""
    from datetime import datetime

    derniere = db.get_parametre("veille_ohada_derniere_verification")
    if not derniere:
        return None
    mois_ecoules = _heures_depuis(derniere) / (24 * 30)
    if mois_ecoules < seuil_mois:
        return None
    return (
        f"Le corpus OHADA (Actes uniformes) n'a pas été revérifié manuellement depuis "
        f"plus de {seuil_mois} mois. Aucune détection automatique n'est possible pour cette "
        "source (pas d'API publique) -- une revérification manuelle est recommandée."
    )


def marquer_veille_ohada_verifiee() -> None:
    """Appelée depuis un bouton explicite de gui.py quand l'avocat confirme
    avoir revérifié manuellement le corpus OHADA contre la source
    officielle -- jamais automatique."""
    from datetime import datetime

    db.set_parametre("veille_ohada_derniere_verification", datetime.now().isoformat(timespec="seconds"))
