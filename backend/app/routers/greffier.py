"""
/api/greffier — Chronologie automatique, extraction d'éléments clés,
classement de document, contrôle de cohérence entre documents, recherche
transversale, rédaction de PV d'audience, vérification procédurale, et
analyse de réquisitoire / rapport d'instruction.

Toute la logique métier vient telle quelle de analyse.py et db.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import os

import analyse as legacy_analyse
import db
import export as legacy_export
from app import demo, demo_data
from app.deps import construire_contexte_dossier, get_dossier_or_404
from app.schemas.greffier import (
    ChronologieIn,
    ChronologieOut,
    ClassementIn,
    ClassementOut,
    CoherenceIn,
    CoherenceOut,
    ExtractionIn,
    ExtractionOut,
    PvAudienceExportIn,
    PvAudienceIn,
    PvAudienceOut,
    RapportInstructionIn,
    RapportInstructionOut,
    RequisitoireIn,
    RequisitoireOut,
    VerificationProceduraleIn,
    VerificationProceduraleOut,
)
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/greffier", tags=["greffier"])


@router.post("/chronologie", response_model=ChronologieOut)
def chronologie(payload: ChronologieIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        return demo_data.CHRONOLOGIE_DEMO
    contexte = construire_contexte_dossier(dossier)
    return legacy_analyse.construire_chronologie(contexte)


@router.post("/extraction", response_model=ExtractionOut)
def extraction(payload: ExtractionIn):
    demo.exiger_cle_api()
    return legacy_analyse.extraire_elements_cles(payload.texte)


@router.post("/classement", response_model=ClassementOut)
def classement(payload: ClassementIn):
    demo.exiger_cle_api()
    return legacy_analyse.classifier_document(payload.texte)


@router.post("/coherence", response_model=CoherenceOut)
def controle_coherence(payload: CoherenceIn):
    """Extrait d'abord les éléments clés de chaque document (mêmes règles
    que /extraction), puis les compare — reproduit exactement le flux de
    PlaidIAApp._action_controle_coherence (gui.py)."""
    demo.exiger_cle_api()
    elements_par_document = []
    elements_par_nom = {}
    for doc in payload.documents:
        elements = legacy_analyse.extraire_elements_cles(doc.texte)
        elements_par_document.append({"nom_document": doc.nom_document, "elements": elements})
        elements_par_nom[doc.nom_document] = elements

    resultat = legacy_analyse.controler_coherence(elements_par_document)
    return CoherenceOut(
        elements_par_document=elements_par_nom,
        contradictions=resultat.get("contradictions", []),
        elements_coherents=resultat.get("elements_coherents", []),
        limites_analyse=resultat.get("limites_analyse", ""),
    )


@router.get("/recherche", response_model=list[dict])
def recherche_transversale(terme: str):
    return db.rechercher_dans_dossiers(terme)


@router.post("/pv-audience", response_model=PvAudienceOut)
def pv_audience(payload: PvAudienceIn):
    demo.exiger_cle_api()
    texte = legacy_analyse.rediger_pv(payload.notes)
    return PvAudienceOut(texte=texte)


@router.post("/pv-audience/export")
def exporter_pv_audience(payload: PvAudienceExportIn):
    """Export Word générique (export.py::exporter_texte_libre_word), sans
    dossier requis -- un PV peut être rédigé avant même la création d'une
    affaire dans l'outil."""
    chemin = legacy_export.exporter_texte_libre_word(payload.titre, payload.texte)
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/verification-procedurale", response_model=VerificationProceduraleOut)
def verification_procedurale(payload: VerificationProceduraleIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    demo.exiger_cle_api()
    contexte = construire_contexte_dossier(dossier)
    return legacy_analyse.verifier_procedure(contexte)


@router.post("/requisitoire", response_model=RequisitoireOut)
def requisitoire(payload: RequisitoireIn):
    demo.exiger_cle_api()
    return legacy_analyse.analyser_requisitoire(payload.texte)


@router.post("/rapport-instruction", response_model=RapportInstructionOut)
def rapport_instruction(payload: RapportInstructionIn):
    demo.exiger_cle_api()
    return legacy_analyse.analyser_rapport_instruction(payload.texte)
