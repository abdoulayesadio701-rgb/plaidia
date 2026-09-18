"""
Calcul déterministe des délais de procédure (aucun appel modèle : une date
limite doit être reproductible et vérifiable, pas générée).

Règles de computation appliquées (art. 640 à 642 CPC, transposées à tous les
délais du catalogue) :
  - le jour de départ (dies a quo) n'est jamais compté ;
  - délai en mois : expire le jour du dernier mois portant le même quantième
    que le jour de départ, à défaut le dernier jour du mois (art. 641 CPC) ;
  - délai en jours francs : ni le jour de départ ni le jour d'échéance ne
    comptent ;
  - échéance un samedi, un dimanche ou un jour férié : prorogée au premier
    jour ouvrable suivant (art. 642 CPC).

Non pris en compte (à vérifier par le greffier) : délais de distance
(art. 643 CPC), causes de suspension ou d'interruption, point de départ
différent de celui du catalogue (notification vs signification).
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class RegleDelai:
    code: str
    libelle: str
    duree: int
    unite: str  # "jours" | "mois"
    jours_francs: bool
    reference: str
    point_de_depart: str


CATALOGUE: dict[str, RegleDelai] = {r.code: r for r in (
    RegleDelai("appel_civil", "Appel d'un jugement civil (matière contentieuse)", 1, "mois", False,
               "art. 538 CPC", "Signification du jugement"),
    RegleDelai("opposition_civil", "Opposition à un jugement rendu par défaut", 1, "mois", False,
               "art. 538 CPC", "Signification du jugement"),
    RegleDelai("appel_refere", "Appel d'une ordonnance de référé", 15, "jours", False,
               "art. 490 CPC", "Signification de l'ordonnance"),
    RegleDelai("pourvoi_civil", "Pourvoi en cassation (matière civile)", 2, "mois", False,
               "art. 612 CPC", "Signification de la décision"),
    RegleDelai("appel_prudhommes", "Appel d'un jugement du conseil de prud'hommes", 1, "mois", False,
               "art. R. 1461-1 C. trav.", "Notification du jugement"),
    RegleDelai("appel_correctionnel", "Appel d'un jugement correctionnel", 10, "jours", False,
               "art. 498 CPP", "Prononcé du jugement contradictoire"),
    RegleDelai("pourvoi_penal", "Pourvoi en cassation (matière pénale)", 5, "jours", True,
               "art. 568 CPP", "Prononcé de la décision"),
    RegleDelai("recours_administratif", "Recours pour excès de pouvoir devant le juge administratif", 2, "mois", False,
               "art. R. 421-1 CJA", "Notification ou publication de la décision"),
)}

AVERTISSEMENT = (
    "Calcul indicatif à vérifier : délais de distance, suspension, interruption et point de départ "
    "réel (signification, notification ou prononcé) ne sont pas pris en compte."
)


def _paques(annee: int) -> date:
    """Dimanche de Pâques (algorithme grégorien anonyme de Meeus/Jones/Butcher)."""
    a = annee % 19
    b, c = divmod(annee, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois, jour = divmod(h + l - 7 * m + 114, 31)
    return date(annee, mois, jour + 1)


def jours_feries(annee: int) -> set[date]:
    paques = _paques(annee)
    return {
        date(annee, 1, 1),
        paques + timedelta(days=1),   # lundi de Pâques
        date(annee, 5, 1),
        date(annee, 5, 8),
        paques + timedelta(days=39),  # Ascension
        paques + timedelta(days=50),  # lundi de Pentecôte
        date(annee, 7, 14),
        date(annee, 8, 15),
        date(annee, 11, 1),
        date(annee, 11, 11),
        date(annee, 12, 25),
    }


def _est_ouvrable(jour: date) -> bool:
    return jour.weekday() < 5 and jour not in jours_feries(jour.year)


def _ajouter_mois(depart: date, mois: int) -> date:
    total = depart.month - 1 + mois
    annee = depart.year + total // 12
    mois_cible = total % 12 + 1
    dernier_jour = calendar.monthrange(annee, mois_cible)[1]
    return date(annee, mois_cible, min(depart.day, dernier_jour))


def calculer_echeance(regle: RegleDelai, date_depart: date) -> tuple[date, date]:
    """Retourne (échéance brute, échéance après prorogation art. 642 CPC)."""
    if regle.unite == "mois":
        brute = _ajouter_mois(date_depart, regle.duree)
    else:
        brute = date_depart + timedelta(days=regle.duree + (1 if regle.jours_francs else 0))
    effective = brute
    while not _est_ouvrable(effective):
        effective += timedelta(days=1)
    return brute, effective


def duree_texte(regle: RegleDelai) -> str:
    if regle.unite == "mois":
        return f"{regle.duree} mois"
    return f"{regle.duree} jours francs" if regle.jours_francs else f"{regle.duree} jours"
