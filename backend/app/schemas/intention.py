"""Schémas Pydantic pour le router /api/intention."""

from typing import Optional

from pydantic import BaseModel, Field


class IntentionIn(BaseModel):
    texte: str = Field(..., min_length=1, description="Commande en langage naturel, ex. « analyser ces conclusions »")


class IntentionOut(BaseModel):
    action: str = "menu"
    confiance: str = "basse"
    reformulation: str = ""
    duree_minutes: Optional[int] = None
