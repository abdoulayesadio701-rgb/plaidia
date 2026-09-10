"""Schémas Pydantic pour le router /api/epingles."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

TypeEpingle = Literal["dossier", "analyse", "document_genere", "conversation"]


class EpinglerIn(BaseModel):
    type: TypeEpingle
    reference_id: int
    dossier_id: Optional[int] = None
    libelle: str = Field(..., min_length=1, max_length=300)


class EpingleOut(BaseModel):
    id: int
    type: str
    reference_id: int
    dossier_id: Optional[int] = None
    libelle: str
    date_creation: str
    cible_titre: Optional[str] = None
    cible_feature: Optional[str] = None
