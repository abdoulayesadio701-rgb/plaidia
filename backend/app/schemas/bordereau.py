"""Schémas Pydantic pour le router /api/bordereau."""

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class PieceIO(BaseModel):
    numero: int = Field(..., ge=1, le=9999)
    intitule: str = Field(..., min_length=1, max_length=300)
    date: str = Field("", max_length=40, description="AAAA-MM-JJ de préférence, saisie libre acceptée")
    produite_par: str = Field("", max_length=100)
    observation: str = Field("", max_length=300)


class BordereauIn(BaseModel):
    pieces: list[PieceIO] = Field(default_factory=list, max_length=300)

    @model_validator(mode="after")
    def numeros_uniques(self):
        numeros = [p.numero for p in self.pieces]
        if len(numeros) != len(set(numeros)):
            raise ValueError("Deux pièces portent le même numéro.")
        return self


class BordereauOut(BaseModel):
    pieces: list[PieceIO] = []
    document_id: Optional[int] = None
