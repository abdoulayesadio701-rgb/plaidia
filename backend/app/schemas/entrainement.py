"""Schémas Pydantic pour le router /api/entrainement."""

from typing import Optional

from pydantic import BaseModel, Field


class SectionMesureeIn(BaseModel):
    point: str = Field(..., min_length=1, max_length=500)
    alloue_secondes: int = Field(..., ge=0, le=3 * 3600)
    reel_secondes: int = Field(..., ge=0, le=6 * 3600)
    traitee: bool = True


class EntrainementIn(BaseModel):
    dossier_id: int
    sections: list[SectionMesureeIn] = Field(..., min_length=1, max_length=50)


class SectionBilanOut(BaseModel):
    point: str
    alloue_secondes: int
    reel_secondes: int
    ecart_secondes: int
    statut: str  # "dans_les_temps" | "depasse" | "en_avance" | "non_traite"


class BilanOut(BaseModel):
    sections: list[SectionBilanOut] = []
    total_alloue_secondes: int = 0
    total_reel_secondes: int = 0
    total_ecart_secondes: int = 0
    document_id: Optional[int] = None
    statut: str = "Brouillon"


class ExportBilanIn(BaseModel):
    dossier_id: int
    sections: list[SectionBilanOut] = []
    total_alloue_secondes: int = 0
    total_reel_secondes: int = 0
    total_ecart_secondes: int = 0
