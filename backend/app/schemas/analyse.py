"""Schémas Pydantic pour le router /api/analyse."""

from typing import Optional

from pydantic import BaseModel, Field

from app.demo import MAX_TEXTE_CARACTERES
from app.schemas.verification import VerificationOut


class ConclusionsIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Texte des conclusions adverses")
    dossier_id: Optional[int] = Field(
        None, description="Si fourni, le résultat est automatiquement enregistré pour ce dossier"
    )


class RaisonnementOut(BaseModel):
    probleme_de_droit: str = ""
    regle_applicable: str = ""
    application_aux_faits: str = ""


class RefutationOut(BaseModel):
    angle: str = ""
    piste: str = ""


class ArgumentOut(BaseModel):
    resume: str = ""
    fondement: str = ""
    raisonnement: Optional[RaisonnementOut] = None
    risque: str = "?"
    justification_risque: str = ""
    refutations: list[RefutationOut] = []


class ConclusionsOut(BaseModel):
    arguments: list[ArgumentOut]
    points_attention: list[str] = []
    analyse_id: Optional[int] = Field(None, description="Id de l'analyse enregistrée en base, si dossier_id était fourni")
    statut: str = "Brouillon"
    verification: Optional[VerificationOut] = Field(
        None, description="Contrôle multi-agents additif (vérificateur juridique, critique, validation finale) — absent en mode démo, voir ARCHITECTURE_MULTI_AGENTS.md"
    )


class StatutDocumentIn(BaseModel):
    statut: str = Field(..., description="Nouveau statut du document")


class StatutDocumentOut(BaseModel):
    analyse_id: int
    statut: str


class ResumeIn(BaseModel):
    dossier_id: int


class ResumeOut(BaseModel):
    resume_court: str = ""
    points_cles: list[str] = []
    elements_manquants: list[str] = []


class PlanIn(BaseModel):
    dossier_id: int
    temps_minutes: int = Field(..., ge=1, le=180, description="Temps de parole imparti, en minutes")


class PointPlanOut(BaseModel):
    point: str = ""
    duree_minutes: Optional[int] = None
    argument_cle: str = ""
    notes: str = ""


class PlanOut(BaseModel):
    accroche: str = ""
    plan: list[PointPlanOut] = []
    conclusion: str = ""
    points_attention: list[str] = []
    verification: Optional[VerificationOut] = None


class SimulateurIn(BaseModel):
    dossier_id: int


class ObjectionOut(BaseModel):
    origine: str = "?"
    question: str = ""
    piege: str = ""
    piste_reponse: str = ""


class SimulateurOut(BaseModel):
    objections: list[ObjectionOut] = []
    point_le_plus_faible: str = ""
    verification: Optional[VerificationOut] = None


class ExportSimulateurIn(BaseModel):
    dossier_id: int
    objections: list[ObjectionOut] = []
    point_le_plus_faible: str = ""


class RapportCompletIn(BaseModel):
    dossier_id: int
    temps_minutes: Optional[int] = Field(None, ge=1, le=180, description="Omis = pas de plan de plaidoirie généré")


class RapportCompletOut(BaseModel):
    analyse: Optional[ConclusionsOut] = None
    plan: Optional[PlanOut] = None
    simulateur: SimulateurOut


class StyleIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES)


class ElementStyleOut(BaseModel):
    citation: str = ""
    commentaire: str = ""


class StyleOut(BaseModel):
    langage_de_couverture: list[ElementStyleOut] = []
    affirmations_absolues: list[ElementStyleOut] = []
    voix_passive_suspecte: list[ElementStyleOut] = []
    ruptures_registre: list[ElementStyleOut] = []
    synthese_strategique: str = ""


class TraductionIn(BaseModel):
    texte: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES, description="Texte à traduire, en français ou en anglais")


class TraductionOut(BaseModel):
    langue_detectee: str = ""
    langue_cible: str = ""
    texte_traduit: str = ""


class ExportAnalyseIn(BaseModel):
    dossier_id: int
    arguments: list[dict]
    points_attention: list[str] = []


class ExportRapportCompletIn(BaseModel):
    dossier_id: int
    analyse: Optional[dict] = None
    plan: Optional[dict] = None
    simulateur: Optional[dict] = None
