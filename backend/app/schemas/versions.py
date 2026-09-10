"""Schémas Pydantic pour le router /api/versions."""

from typing import Optional

from pydantic import BaseModel


class VersionOut(BaseModel):
    id: int
    dossier_id: Optional[int] = None
    document_id: Optional[int] = None
    feature: str
    contenu: dict
    resume_modification: Optional[str] = ""
    auteur: str
    date_creation: str
