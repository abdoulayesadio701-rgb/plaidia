"""Schémas Pydantic pour le router /api/generations.

Distinct de /api/documents-generes (schemas/documents.py) : celui-ci suit
le statut ÉDITORIAL d'un document (Brouillon -> ... -> Final). Ici, le
statut est TECHNIQUE (en_cours -> terminee | erreur) et reflète le
traitement IA lui-même -- voir db.py, section "Générations"."""

from typing import Optional

from pydantic import BaseModel


class GenerationLanceeOut(BaseModel):
    """Réponse immédiate (202) au lancement d'une génération en
    arrière-plan -- le contenu n'est pas encore prêt, seul l'id permet de
    suivre son avancement via GET /api/generations/{id}."""

    id: int
    statut: str = "en_cours"


class GenerationOut(BaseModel):
    id: int
    type: str
    dossier_id: Optional[int] = None
    libelle: str
    contenu: Optional[dict] = None
    statut: str
    erreur: Optional[str] = None
    date_creation: str
    date_fin: Optional[str] = None
