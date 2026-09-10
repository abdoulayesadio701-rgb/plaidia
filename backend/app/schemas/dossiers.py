"""Schémas Pydantic pour le router /api/dossiers."""

from typing import Optional

from pydantic import BaseModel, Field

from app.demo import MAX_TEXTE_CARACTERES


class DossierCreate(BaseModel):
    nom: str = Field(..., min_length=1, max_length=300, description="Nom du dossier")
    numero_dossier: str = Field("", max_length=100, description="Numéro de référence (optionnel)")
    domaine: str = Field("", max_length=200, description="Domaine (Prud'hommes, Pénal, Civil...)")
    parties: str = Field("", max_length=MAX_TEXTE_CARACTERES, description="Parties au dossier (optionnel)")
    faits: str = Field("", max_length=MAX_TEXTE_CARACTERES, description="Faits connus au moment de la création (optionnel)")


class DossierDomaineUpdate(BaseModel):
    domaine: str = Field(..., description="Nouveau domaine du dossier")


class DossierOut(BaseModel):
    id: int
    nom: str
    numero_dossier: Optional[str] = ""
    domaine: Optional[str] = ""
    parties: Optional[str] = ""
    faits: Optional[str] = ""
    statut: str
    date_creation: str


class FaitsAjout(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Texte à ajouter aux faits du dossier")
    source: str = Field("texte collé", max_length=300, description="Origine du texte (nom de fichier, « texte collé »...)")


class DocumentImporteOut(BaseModel):
    nom_fichier: str
    texte_extrait: str
    caracteres_extraits: int


class RechercheDossierResultat(BaseModel):
    dossier: DossierOut
    extraits: list[tuple[str, str]]


class AnalyseHistoriqueOut(BaseModel):
    id: int
    date: str
    arguments: list[dict]
    points_attention: list[str]
    statut: str = "Brouillon"
