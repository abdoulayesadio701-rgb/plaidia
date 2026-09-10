"""Schémas des documents générés persistés par dossier."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentGenereOut(BaseModel):
    id: int
    dossier_id: int
    feature: str
    titre: str
    parametres: dict[str, Any]
    contenu: dict[str, Any]
    statut: str
    date_creation: str
    date_modification: str


class DocumentStatutIn(BaseModel):
    statut: str = Field(..., description="Nouveau statut du document")


class DocumentStatutOut(BaseModel):
    id: int
    statut: str


class DocumentVersionOut(BaseModel):
    id: int
    document_id: Optional[int] = None
    statut: str
