"""
Bilan d'un entraînement chronométré à la plaidoirie : compare, section par
section, le temps alloué par le plan de plaidoirie au temps réellement passé.
Aucun appel modèle : c'est de l'arithmétique sur des durées mesurées.
"""

from __future__ import annotations

# Une section est « dans les temps » si l'écart reste sous 10 % du temps
# alloué, avec un plancher de 10 secondes (sinon une section de 30 s serait
# jugée sur 3 s d'écart, ce qui n'a pas de sens à l'oral).
TOLERANCE_RELATIVE = 0.10
TOLERANCE_MINIMALE_SECONDES = 10

DANS_LES_TEMPS = "dans_les_temps"
DEPASSE = "depasse"
EN_AVANCE = "en_avance"
NON_TRAITE = "non_traite"


def statut_section(alloue: int, reel: int, traitee: bool) -> str:
    if not traitee:
        return NON_TRAITE
    tolerance = max(TOLERANCE_MINIMALE_SECONDES, round(alloue * TOLERANCE_RELATIVE))
    ecart = reel - alloue
    if ecart > tolerance:
        return DEPASSE
    if ecart < -tolerance:
        return EN_AVANCE
    return DANS_LES_TEMPS


def construire_bilan(sections: list[dict]) -> dict:
    """`sections` : [{point, alloue_secondes, reel_secondes, traitee}]. Le total
    ne compte que les sections traitées, pour qu'un entraînement arrêté en
    cours de route ne soit pas présenté comme « très en avance »."""
    lignes = []
    total_alloue = 0
    total_reel = 0
    for s in sections:
        alloue = int(s["alloue_secondes"])
        reel = int(s["reel_secondes"])
        traitee = bool(s.get("traitee", True))
        lignes.append({
            "point": s["point"],
            "alloue_secondes": alloue,
            "reel_secondes": reel,
            "ecart_secondes": reel - alloue if traitee else 0,
            "statut": statut_section(alloue, reel, traitee),
        })
        if traitee:
            total_alloue += alloue
            total_reel += reel
    return {
        "sections": lignes,
        "total_alloue_secondes": total_alloue,
        "total_reel_secondes": total_reel,
        "total_ecart_secondes": total_reel - total_alloue,
    }


def formater_duree(secondes: int) -> str:
    signe = "-" if secondes < 0 else ""
    minutes, reste = divmod(abs(secondes), 60)
    return f"{signe}{minutes} min {reste:02d} s"
