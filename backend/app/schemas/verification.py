"""Schémas Pydantic partagés pour le bloc `verification` additif produit par
le pipeline multi-agents (voir backend/app/quality_pipeline.py et
ARCHITECTURE_MULTI_AGENTS.md §6-7).

Toujours un champ OPTIONNEL ajouté aux schémas *Out existants (ConclusionsOut,
PlanOut, SimulateurOut, ConsulterOut) -- jamais un champ existant renommé ou
supprimé. Un front qui ignore `verification` continue de fonctionner à
l'identique."""

from pydantic import BaseModel


class ElementVerifieOut(BaseModel):
    affirmation: str = ""
    statut: str = "A_VERIFIER"  # VERIFIE | PARTIELLEMENT_VERIFIE | A_VERIFIER | NON_VERIFIE
    commentaire: str = ""


class CritiqueOut(BaseModel):
    cible: str = ""
    type: str = ""
    commentaire: str = ""
    gravite: str = "Faible"  # Faible | Moyenne | Élevée


class VerificationOut(BaseModel):
    statut_global: str = "A_VERIFIER"  # VERIFIE | A_VERIFIER | INCERTAIN
    elements: list[ElementVerifieOut] = []
    critiques: list[CritiqueOut] = []
    points_a_verifier: list[str] = []
    synthese_utilisateur: str = ""
