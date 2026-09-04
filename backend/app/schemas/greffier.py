"""Schémas Pydantic pour le router /api/greffier."""

from pydantic import BaseModel, Field

from app.demo import MAX_TEXTE_CARACTERES


class ChronologieIn(BaseModel):
    dossier_id: int


class EvenementOut(BaseModel):
    date: str = "?"
    evenement: str = ""


class ChronologieOut(BaseModel):
    periode_couverte: str = "non déterminée"
    evenements: list[EvenementOut] = []
    elements_manquants: list[str] = []


class ExtractionIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Texte du document à traiter")


class ExtractionOut(BaseModel):
    dates: list[str] = []
    personnes_et_parties: list[str] = []
    references: list[str] = []
    demandes: list[str] = []
    decisions: list[str] = []


class ClassementIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES)


class ClassementOut(BaseModel):
    nature: str = "autre"
    justification: str = ""
    confiance: str = "Faible"


class DocumentACoherence(BaseModel):
    nom_document: str = Field(..., min_length=1, max_length=200)
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES)


class CoherenceIn(BaseModel):
    documents: list[DocumentACoherence] = Field(..., min_length=2, description="Au moins deux documents requis")


class ContradictionOut(BaseModel):
    sujet: str = ""
    document_1: str = ""
    document_2: str = ""
    gravite: str = "?"


class CoherenceOut(BaseModel):
    elements_par_document: dict[str, ExtractionOut]
    contradictions: list[ContradictionOut] = []
    elements_coherents: list[str] = []
    limites_analyse: str = ""


class RechercheTransversaleOut(BaseModel):
    dossier: dict
    extraits: list[tuple[str, str]]


class PvAudienceIn(BaseModel):
    notes: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Notes prises pendant l'audience")


class PvAudienceOut(BaseModel):
    texte: str


class PvAudienceExportIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Texte du PV, éventuellement retouché après génération")
    titre: str = Field("Procès-verbal d'audience", description="Titre du document Word exporté")


class VerificationProceduraleIn(BaseModel):
    dossier_id: int


class EcheanceOut(BaseModel):
    echeance: str = ""
    date: str = "non précisée"
    statut: str = "Date incertaine"


class VerificationProceduraleOut(BaseModel):
    echeances_identifiees: list[EcheanceOut] = []
    actes_potentiellement_manquants: list[str] = []
    points_attention: list[str] = []


class RequisitoireIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Texte du réquisitoire")


class RequisitoireOut(BaseModel):
    qualification_retenue: str = ""
    faits_et_elements_invoques: list[str] = []
    circonstances_aggravantes: list[str] = []
    circonstances_attenuantes: list[str] = []
    peine_requise: str = "non précisée"
    points_attention: list[str] = []


class RapportInstructionIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Texte du rapport d'instruction")


class RapportInstructionOut(BaseModel):
    actes_instruction: list[str] = []
    elements_a_charge: list[str] = []
    elements_a_decharge: list[str] = []
    mesures_ordonnees: list[str] = []
    sens_propose: str = "non précisé"
    points_attention: list[str] = []
