"""
Bordereau de pièces d'un dossier : liste numérotée des pièces communiquées.
Aucun appel modèle : c'est une donnée saisie par l'utilisateur.
"""

from __future__ import annotations

import re
from datetime import date

# En-tête posé par db.ajouter_aux_faits : « --- Document importé le
# 12/03/2026 10:30 (nom.pdf) --- ». La source est absente pour un texte sans
# nom, et vaut « texte collé » pour un texte collé : ce ne sont pas des pièces.
_RE_ENTETE_IMPORT = re.compile(r"^--- Document importé le [\d/]+ [\d:]+(?: \((.+)\))? ---$", re.MULTILINE)
SOURCES_NON_PIECES = {"texte collé", "document importé"}


def extraire_sources(faits: str) -> list[str]:
    """Noms des documents importés dans les faits, sans doublon, dans l'ordre
    d'import."""
    vues: list[str] = []
    for correspondance in _RE_ENTETE_IMPORT.finditer(faits or ""):
        nom = (correspondance.group(1) or "").strip()
        if nom and nom.lower() not in SOURCES_NON_PIECES and nom not in vues:
            vues.append(nom)
    return vues


def formater_date(valeur: str) -> str:
    """AAAA-MM-JJ -> JJ/MM/AAAA ; toute autre saisie est gardée telle quelle."""
    try:
        return date.fromisoformat(valeur).strftime("%d/%m/%Y")
    except ValueError:
        return valeur
