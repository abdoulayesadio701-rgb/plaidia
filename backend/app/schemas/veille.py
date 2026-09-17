"""Schémas Pydantic pour le router /api/veille."""

from typing import Optional

from pydantic import BaseModel


class AlerteJurisprudenceOut(BaseModel):
    id: int
    dossier_id: int
    reference: str
    resume: Optional[str] = None
    source: Optional[str] = None
    date_detection: str
    statut: str


class AlerteArticleOut(BaseModel):
    id: int
    dossier_id: int
    code: str
    numero: str
    ancien_etat: Optional[str] = None
    nouvel_etat: Optional[str] = None
    date_modification: Optional[str] = None
    lien_source: Optional[str] = None
    date_detection: str
    statut: str


class NotificationsVeilleOut(BaseModel):
    jurisprudence: list[AlerteJurisprudenceOut]
    lois: list[AlerteArticleOut]
    rappel_ohada: Optional[str] = None
