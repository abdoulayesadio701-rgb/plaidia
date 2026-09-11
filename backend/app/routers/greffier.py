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
from app import demo, demo_data, quality_pipeline
from app.deps import construire_contexte_dossier, get_dossier_or_404
from app.security_guard import executer_garde_fou
from app.schemas.greffier import (
    ChronologieIn,
    ChronologieOut,
    ClassementIn,
    ClassementOut,
    CoherenceIn,
    CoherenceOut,
    ExportChronologieIn,
    ExportVerificationProceduraleIn,
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


@router.post("/chronologie/export")
def exporter_chronologie(payload: ExportChronologieIn):
    """Export CSV (export.py::exporter_csv) -- une chronologie est un
    tableau (date, événement), un tableur est plus utile qu'un document
    Word pour la retrier/filtrer ensuite (voir AUDIT_IMPORT_EXPORT.md §6)."""
    dossier = get_dossier_or_404(payload.dossier_id)
    lignes = [[e.date, e.evenement] for e in payload.evenements]
    chemin = legacy_export.exporter_csv(
        f"{dossier['nom']} — {legacy_export._l('chronologie_titre')}",
        [legacy_export._l("date"), legacy_export._l("evenement")],
        lignes,
    )
    return FileResponse(chemin, filename=os.path.basename(chemin), media_type="text/csv")


@router.post("/extraction", response_model=ExtractionOut)
def extraction(payload: ExtractionIn):
    """Route vers DeepSeek (voir analyse.TypeTache.EXTRACTION) -- garde-fou
    d'entrée et contrôle déterministe des citations ajoutés ici en même
    temps que le changement de fournisseur : ils manquaient déjà sous
    Claude sur cette route (contrairement à /api/analyse/conclusions), ce
    n'est pas spécifique à DeepSeek."""
    demo.exiger_cle_api()
    demo.exiger_cle_api_deepseek()
    executer_garde_fou(payload.texte)
    elements = legacy_analyse.extraire_elements_cles(payload.texte)
    for ref in elements.get("references", []):
        citations = quality_pipeline.verifier_citations_deterministe(str(ref), [payload.texte])
        for c in citations:
            if c["statut_deterministe"] != "VERIFIE":
                print(f"[greffier] citation non vérifiée dans une extraction DeepSeek : {c}", flush=True)
    return elements


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


@router.post("/verification-procedurale/export")
def exporter_verification_procedurale(payload: ExportVerificationProceduraleIn):
    """Export Word générique -- rapport à archiver ou transmettre, seule
    fonctionnalité sans export du couple avocat/greffier concerné (voir
    AUDIT_IMPORT_EXPORT.md)."""
    dossier = get_dossier_or_404(payload.dossier_id)
    lignes = []
    if payload.echeances_identifiees:
        lignes.append("ÉCHÉANCES IDENTIFIÉES")
        for e in payload.echeances_identifiees:
            lignes.append(f"- {e.echeance} — {e.date} ({e.statut})")
        lignes.append("")
    if payload.actes_potentiellement_manquants:
        lignes.append("ACTES POTENTIELLEMENT MANQUANTS")
        for a in payload.actes_potentiellement_manquants:
            lignes.append(f"- {a}")
        lignes.append("")
    if payload.points_attention:
        lignes.append("POINTS D'ATTENTION")
        for p in payload.points_attention:
            lignes.append(f"- {p}")
    texte = "\n".join(lignes)

    chemin = legacy_export.exporter_texte_libre_word(
        f"{dossier['nom']} — Vérification procédurale",
        texte,
        note_bas_page="Analyse automatisée à vérifier manuellement -- ne remplace pas le contrôle d'un professionnel du droit.",
    )
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/requisitoire", response_model=RequisitoireOut)
def requisitoire(payload: RequisitoireIn):
    demo.exiger_cle_api()
    return legacy_analyse.analyser_requisitoire(payload.texte)


@router.post("/rapport-instruction", response_model=RapportInstructionOut)
def rapport_instruction(payload: RapportInstructionIn):
    demo.exiger_cle_api()
    return legacy_analyse.analyser_rapport_instruction(payload.texte)
