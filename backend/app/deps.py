"""
deps.py — Petits utilitaires partagés entre routers : récupération d'un
dossier (404 si absent) et construction du "contexte dossier" textuel
envoyé aux fonctions d'analyse — reproduit fidèlement `_contexte_dossier()`
de gui.py, seul endroit où cette logique existait jusqu'ici.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import db
from fastapi import HTTPException


def get_dossier_or_404(dossier_id: int) -> dict:
    """Récupère un dossier en base ou lève une 404 JSON exploitable côté front."""
    row = db.get_dossier(dossier_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Dossier {dossier_id} introuvable.")
    return dict(row)


def construire_contexte_dossier(dossier: dict) -> str:
    """Reproduit PlaidIAApp._contexte_dossier() (gui.py) : agrège faits,
    parties et la dernière analyse enregistrée en un texte que les fonctions
    d'analyse.py utilisent comme `contexte_dossier` / `contexte_affaire`."""
    parts = []
    if dossier.get("faits"):
        parts.append(f"Faits : {dossier['faits']}")
    if dossier.get("parties"):
        parts.append(f"Parties : {dossier['parties']}")

    analyses = db.get_analyses_for_dossier(dossier["id"])
    if analyses:
        derniere = analyses[0]
        parts.append("Arguments adverses déjà analysés :")
        for arg in derniere["arguments"]:
            parts.append(f"- [{arg.get('risque', '?')}] {arg.get('resume', '')}")

    return "\n".join(parts) if parts else f"Dossier « {dossier['nom']} », domaine : {dossier.get('domaine', '')}."
