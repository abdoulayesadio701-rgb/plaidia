"""Schémas Pydantic pour le router /api/notes."""

from typing import Optional

from pydantic import BaseModel, Field

from app.demo import MAX_TEXTE_CARACTERES


class NoteCreate(BaseModel):
    dossier_id: int
    note_brute: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Note telle que saisie, sous n'importe quelle forme")


class NoteOut(BaseModel):
    id: int
    note_brute: str
    note_structuree: Optional[str] = ""
    actions: list[str] = []
    points: list[str] = []
    date_creation: str


class NoteClientIn(BaseModel):
    dossier_id: int


class NoteClientOut(BaseModel):
    texte: str


class ExportNoteClientIn(BaseModel):
    dossier_id: int
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES)
