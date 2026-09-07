"""
/api/analyse — Analyse de conclusions adverses, résumé, plan de plaidoirie,
simulateur d'objections, rapport complet, analyse stylistique, et export
Word/PDF des résultats.

Toute la logique métier vient telle quelle de analyse.py, db.py et export.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import concurrent.futures
import os

import analyse as legacy_analyse
import db
import export as legacy_export
from app import demo, demo_data
from app.deps import construire_contexte_dossier, get_dossier_or_404
from app.schemas.analyse import (
    ConclusionsIn,
    ConclusionsOut,
    ExportAnalyseIn,
    ExportRapportCompletIn,
    PlanIn,
    PlanOut,
    RapportCompletIn,
    RapportCompletOut,
    ResumeIn,
    ResumeOut,
    SimulateurIn,
    SimulateurOut,
    StyleIn,
    StyleOut,
    TraductionIn,
    TraductionOut,
)
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from typing import Literal

router = APIRouter(prefix="/api/analyse", tags=["analyse"])


@router.post("/conclusions", response_model=ConclusionsOut)
def analyser_conclusions(payload: ConclusionsIn):
    if demo.mode_demo_effectif():
        # Réponse préenregistrée, quel que soit le texte fourni -- jamais
        # persistée (voir le bandeau "Mode démo" : données non conservées).
        resultat = demo_data.CONCLUSIONS_DEMO
        if payload.dossier_id is not None:
            get_dossier_or_404(payload.dossier_id)
        return ConclusionsOut(arguments=resultat["arguments"], points_attention=resultat["points_attention"], analyse_id=None)

    resultat = legacy_analyse.analyser_conclusions(payload.texte)
    analyse_id = None
    if payload.dossier_id is not None:
        get_dossier_or_404(payload.dossier_id)
        analyse_id = db.save_analyse(
            payload.dossier_id, resultat.get("arguments", []), resultat.get("points_attention", [])
        )
    return ConclusionsOut(
        arguments=resultat.get("arguments", []),
        points_attention=resultat.get("points_attention", []),
        analyse_id=analyse_id,
    )


@router.post("/resume", response_model=ResumeOut)
def resumer_dossier(payload: ResumeIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        return demo_data.RESUME_DEMO
    contexte = construire_contexte_dossier(dossier)
    return legacy_analyse.resumer_dossier(contexte)


@router.post("/plan", response_model=PlanOut)
def generer_plan(payload: PlanIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        return demo_data.PLAN_DEMO
    contexte = construire_contexte_dossier(dossier)
    return legacy_analyse.generer_plan_plaidoirie(contexte, payload.temps_minutes)


@router.post("/simulateur", response_model=SimulateurOut)
def simuler_objections(payload: SimulateurIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        return demo_data.SIMULATEUR_DEMO
    contexte = construire_contexte_dossier(dossier)
    return legacy_analyse.simuler_objections(contexte)


@router.post("/rapport-complet", response_model=RapportCompletOut)
def rapport_complet(payload: RapportCompletIn):
    dossier = get_dossier_or_404(payload.dossier_id)

    if demo.mode_demo_effectif():
        plan_result = demo_data.PLAN_DEMO if payload.temps_minutes else None
        return RapportCompletOut(analyse=demo_data.CONCLUSIONS_DEMO, plan=plan_result, simulateur=demo_data.SIMULATEUR_DEMO)

    contexte = construire_contexte_dossier(dossier)

    analyses_existantes = db.get_analyses_for_dossier(payload.dossier_id)
    analyse_result = None
    if analyses_existantes:
        derniere = analyses_existantes[0]
        analyse_result = {"arguments": derniere["arguments"], "points_attention": derniere["points_attention"]}

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    try:
        future_plan = (
            executor.submit(legacy_analyse.generer_plan_plaidoirie, contexte, payload.temps_minutes)
            if payload.temps_minutes
            else None
        )
        future_sim = executor.submit(legacy_analyse.simuler_objections, contexte)
        plan_result = future_plan.result() if future_plan else None
        sim_result = future_sim.result()
    finally:
        executor.shutdown(wait=False)

    return RapportCompletOut(analyse=analyse_result, plan=plan_result, simulateur=sim_result)


@router.post("/style", response_model=StyleOut)
def analyser_style(payload: StyleIn):
    demo.exiger_cle_api()
    return legacy_analyse.analyser_style_adverse(payload.texte)


@router.post("/traduire", response_model=TraductionOut)
def traduire(payload: TraductionIn):
    demo.exiger_cle_api()
    return legacy_analyse.traduire_texte(payload.texte)


@router.post("/conclusions/export")
def exporter_conclusions(payload: ExportAnalyseIn, format: Literal["word", "pdf"] = Query("word")):
    dossier = get_dossier_or_404(payload.dossier_id)
    result = {"arguments": payload.arguments, "points_attention": payload.points_attention}
    if format == "word":
        chemin = legacy_export.exporter_word(dossier, result)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        chemin = legacy_export.exporter_pdf(dossier, result)
        media_type = "application/pdf"
    return FileResponse(chemin, filename=os.path.basename(chemin), media_type=media_type)


@router.post("/rapport-complet/export")
def exporter_rapport_complet(payload: ExportRapportCompletIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    chemin = legacy_export.exporter_dossier_complet_word(dossier, payload.analyse, payload.plan, payload.simulateur)
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
