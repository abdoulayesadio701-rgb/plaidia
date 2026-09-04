"""Schémas Pydantic pour le router /api/jurisprudence."""

from typing import Optional

from pydantic import BaseModel, Field

from app.demo import MAX_TEXTE_CARACTERES


class ConsulterIn(BaseModel):
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
