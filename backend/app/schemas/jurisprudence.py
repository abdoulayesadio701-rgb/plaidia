"""Schémas Pydantic pour le router /api/jurisprudence."""

from typing import Optional

from pydantic import BaseModel, Field

from app.demo import MAX_TEXTE_CARACTERES
from app.schemas.verification import VerificationOut


class ConsulterIn(BaseModel):
    dossier_id: int = Field(..., description="Dossier auquel rattacher la consultation")
    question: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Situation ou question juridique décrite librement")
    but: str = Field("", max_length=500, description="Ex. « Décisions favorables à mon client », laisser vide pour neutre")
    source: str = Field("Légifrance (France)", description="Juridiction active (Légifrance ou une source de corpus importée)")


class NotionsOut(BaseModel):
    domaine: str = ""
    qualification_juridique: str = ""
    mots_cles_recherche: list[str] = []
    but: str = ""


class ConsulterOut(BaseModel):
    notions: NotionsOut
    reponse: str
    verification: Optional[VerificationOut] = None
    document_id: Optional[int] = None
    statut: str = "Brouillon"


class CollecterIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Mots-clés de recherche Judilibre")
    domaine: str = Field("", max_length=200, description="Domaine associé (optionnel)")


class DecisionCollecteeOut(BaseModel):
    reference: str
    resume: str
    domaine: str = ""
    source: str = ""


class CollecterOut(BaseModel):
    decisions: list[DecisionCollecteeOut]
    nombre_collecte: int


class JurisprudenceOut(BaseModel):
    id: int
    reference: str
    resume: Optional[str] = ""
    domaine: Optional[str] = ""
    source: Optional[str] = ""
    validee: int


class CorpusImportIn(BaseModel):
    source: str = Field(..., max_length=200, description="Ex. OHADA, Union européenne, Droit sénégalais...")
    contenu: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES)
    pays: str = ""
    type_texte: str = ""
    domaine: str = ""
    reference: str = ""
    date_texte: str = ""


class ValiderCorpusSourceIn(BaseModel):
    source: str = Field(..., min_length=1, max_length=200, description="Source exacte (ex. OHADA) dont valider les textes en attente")
    domaine: str = Field("", max_length=300, description="Optionnel : restreint la validation à ce domaine précis au sein de la source (ex. un seul acte uniforme)")


class ValiderCorpusSourceOut(BaseModel):
    source: str
    domaine: str = ""
    nombre_valide: int


class CorpusOut(BaseModel):
    id: int
    source: str
    pays: Optional[str] = ""
    type_texte: Optional[str] = ""
    domaine: Optional[str] = ""
    reference: Optional[str] = ""
    date_texte: Optional[str] = ""
    statut: Optional[str] = ""
    contenu: str
    validee: int
    date_import: str


class JuridictionActiveIn(BaseModel):
    juridiction: str = Field(..., min_length=1)


class JuridictionActiveOut(BaseModel):
    juridiction: str
