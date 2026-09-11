"""
/api/analyse — Analyse de conclusions adverses, résumé, plan de plaidoirie,
simulateur d'objections, rapport complet, analyse stylistique, et export
Word/PDF des résultats.

Toute la logique métier vient telle quelle de analyse.py, db.py et export.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import concurrent.futures
import os
import time

import analyse as legacy_analyse
import db
import export as legacy_export
from app import demo, demo_data, quality_pipeline
from app.deps import construire_contexte_dossier, get_dossier_or_404, sse_event, structurer_sortie_strategique
from app.schemas.analyse import (
    ConclusionsIn,
    ConclusionsOut,
    ExportAnalyseIn,
    ExportRapportCompletIn,
    ExportSimulateurIn,
    PlanIn,
    PlanOut,
    RapportCompletIn,
    RapportCompletOut,
    ResumeIn,
    ResumeOut,
    SimulateurIn,
    SimulateurOut,
    StatutDocumentIn,
    StatutDocumentOut,
    StyleIn,
    StyleOut,
    TraductionIn,
    TraductionOut,
)
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import Literal

router = APIRouter(prefix="/api/analyse", tags=["analyse"])


def _duree_ms(t0: float) -> int:
    return int((time.monotonic() - t0) * 1000)


def _strategie_combative_si_pertinente(
    dossier: dict | None, contexte_dossier: str, arguments_adverses: list[dict] | None = None
) -> dict | None:
    """Complément posture/stratégie : n'appelle l'agent de stratégie
    combative (analyse.generer_strategie_combative) que lorsqu'une partie
    représentée est renseignée -- sinon la stratégie reste générique (voir
    structurer_sortie_strategique), inutile d'appeler le modèle pour un
    résultat qui ne serait pas orienté. Jamais appelé en mode démo (les
    branches démo des endpoints ci-dessous ne l'invoquent pas)."""
    if not dossier:
        return None
    posture = (dossier.get("partie_representee") or "").strip()
    if not posture:
        return None
    return quality_pipeline.executer_strategie_combative(
        lambda: legacy_analyse.generer_strategie_combative(
            contexte_dossier, posture, dossier.get("objectif") or "", arguments_adverses
        )
    )


@router.post("/conclusions", response_model=ConclusionsOut)
def analyser_conclusions(payload: ConclusionsIn):
    dossier = get_dossier_or_404(payload.dossier_id) if payload.dossier_id is not None else None
    if demo.mode_demo_effectif():
        # Réponse préenregistrée, quel que soit le texte fourni -- jamais
        # persistée (voir le bandeau "Mode démo" : données non conservées).
        resultat = demo_data.CONCLUSIONS_DEMO
        sections = structurer_sortie_strategique(resultat, dossier or {"id": 0, "nom": "", "faits": "", "parties": ""}, "conclusions")
        return ConclusionsOut(
            arguments=resultat["arguments"],
            points_attention=resultat["points_attention"],
            analyse_id=None,
            diagnostic=sections["diagnostic"],
            strategie=sections["strategie"],
        )

    # Pipeline complet (§9 ARCHITECTURE_MULTI_AGENTS.md) : garde-fou d'entrée
    # -> agent principal (inchangé) -> vérificateur juridique -> critique ->
    # validation finale. Le texte source lui-même sert de référence au
    # contrôle déterministe des citations (analyser_conclusions ne cite
    # normalement que ce qui figure dans les conclusions adverses fournies).
    contexte_dossier = construire_contexte_dossier(dossier) if dossier else ""
    pipeline = quality_pipeline.executer_pipeline_complet(
        feature="conclusions",
        texte_a_screener=payload.texte,
        # §2e du chantier "temps de traitement" : découpe le texte en
        # moyens et les analyse en parallèle -- reste séquentiel et
        # identique à avant ce chantier si un seul moyen est détecté.
        fonction_principale=lambda: legacy_analyse.analyser_conclusions_par_moyens(payload.texte),
        sources_textes=[payload.texte],
        contexte_dossier=contexte_dossier,
    )
    resultat = pipeline.resultat_principal
    analyse_id = None
    if payload.dossier_id is not None:
        analyse_id = db.save_analyse(
            payload.dossier_id, resultat.get("arguments", []), resultat.get("points_attention", []), langue=legacy_analyse.langue_requete()
        )
    strategie_combative = _strategie_combative_si_pertinente(dossier, contexte_dossier, resultat.get("arguments", []))
    sections = structurer_sortie_strategique(
        {"arguments": resultat.get("arguments", []), "points_attention": resultat.get("points_attention", [])},
        dossier or {"id": 0, "nom": "", "faits": "", "parties": ""},
        "conclusions",
        strategie_combative=strategie_combative,
    )
    return ConclusionsOut(
        arguments=resultat.get("arguments", []),
        points_attention=resultat.get("points_attention", []),
        analyse_id=analyse_id,
        verification=pipeline.verification,
        diagnostic=sections["diagnostic"],
        strategie=sections["strategie"],
    )


@router.post("/conclusions/stream")
def analyser_conclusions_stream(payload: ConclusionsIn):
    """Variante en streaming SSE de POST /conclusions (chantier "temps de
    traitement des générations", §2a) : le résultat de l'agent principal est
    émis dès qu'il est prêt (évènement "principal"), sans attendre le
    vérificateur ni le critique -- leurs statuts arrivent ensuite, dans un
    évènement séparé ("verification"). Même logique métier que /conclusions,
    pas dupliquée : cet endpoint orchestre, il ne réanalyse rien.

    Non disponible en mode démo (rien à streamer, la réponse préenregistrée
    est déjà instantanée) -- utiliser /conclusions dans ce cas."""
    dossier = get_dossier_or_404(payload.dossier_id) if payload.dossier_id is not None else None
    if demo.mode_demo_effectif():
        raise HTTPException(status_code=400, detail="Le streaming n'est pas disponible en mode démo -- utilisez /api/analyse/conclusions.")

    def event_stream():
        trace: list[quality_pipeline.EtapeTrace] = []
        try:
            t0 = time.monotonic()
            yield sse_event("etape", {"etape": "garde_fou", "libelle": "Vérification de la demande"})
            garde = quality_pipeline.executer_garde_fou(payload.texte)
            trace.append(quality_pipeline.EtapeTrace("garde_fou_entree", "ok", _duree_ms(t0), garde.get("reason", "")))

            t0 = time.monotonic()
            yield sse_event("etape", {"etape": "analyse", "libelle": "Analyse des conclusions en cours"})
            resultat = legacy_analyse.analyser_conclusions_par_moyens(payload.texte)
            trace.append(quality_pipeline.EtapeTrace("agent_principal", "ok", _duree_ms(t0)))

            contexte_dossier = construire_contexte_dossier(dossier) if dossier else ""
            strategie_combative = _strategie_combative_si_pertinente(dossier, contexte_dossier, resultat.get("arguments", []))
            sections = structurer_sortie_strategique(
                {"arguments": resultat.get("arguments", []), "points_attention": resultat.get("points_attention", [])},
                dossier or {"id": 0, "nom": "", "faits": "", "parties": ""},
                "conclusions",
                strategie_combative=strategie_combative,
            )
            yield sse_event("principal", {
                "arguments": sections["arguments"],
                "points_attention": sections["points_attention"],
                "diagnostic": sections["diagnostic"],
                "strategie": sections["strategie"],
                "statut": "Brouillon",
            })

            yield sse_event("etape", {"etape": "verification", "libelle": "Vérification des sources et critique"})
            verification, trace_trio = quality_pipeline.executer_trio_qualite(
                quality_pipeline.texte_pour_verification(resultat), [payload.texte], contexte_dossier
            )
            trace.extend(trace_trio)
            yield sse_event("verification", {"verification": verification})

            analyse_id = None
            if payload.dossier_id is not None:
                analyse_id = db.save_analyse(
                    payload.dossier_id, resultat.get("arguments", []), resultat.get("points_attention", []),
                    langue=legacy_analyse.langue_requete(),
                )
            yield sse_event("document", {"analyse_id": analyse_id})

            quality_pipeline.log_trace("conclusions (stream)", trace)
            yield sse_event("done", {})
        except quality_pipeline.DemandeRefusee as e:
            yield sse_event("error", {"detail": e.reason, "risk_level": e.risk_level})
        except Exception as e:
            yield sse_event("error", {"detail": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.patch("/conclusions/{analyse_id}/statut", response_model=StatutDocumentOut)
def changer_statut_conclusions(analyse_id: int, payload: StatutDocumentIn):
    try:
        analyse = db.changer_statut_analyse(analyse_id, payload.statut)
    except db.TransitionStatutInvalide as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    if not analyse:
        raise HTTPException(status_code=404, detail=f"Analyse {analyse_id} introuvable.")
    return {"analyse_id": analyse_id, "statut": analyse["statut"]}


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
        resultat = structurer_sortie_strategique(demo_data.PLAN_DEMO, dossier, "plan")
    else:
        contexte = construire_contexte_dossier(dossier)
        pipeline = quality_pipeline.executer_pipeline_complet(
            feature="plan",
            texte_a_screener=contexte,
            fonction_principale=lambda: legacy_analyse.generer_plan_plaidoirie(contexte, payload.temps_minutes),
            sources_textes=[contexte],
            contexte_dossier=contexte,
        )
        strategie_combative = _strategie_combative_si_pertinente(dossier, contexte)
        resultat = structurer_sortie_strategique(
            {**pipeline.resultat_principal, "verification": pipeline.verification}, dossier, "plan", strategie_combative=strategie_combative
        )
    document = db.creer_document_genere(
        payload.dossier_id, "plan", f"Plan de plaidoirie — {dossier['nom']}", {"temps_minutes": payload.temps_minutes}, resultat,
        langue=legacy_analyse.langue_requete(),
    )
    return PlanOut(**resultat, document_id=document["id"], statut=document["statut"])


@router.post("/plan/stream")
def generer_plan_stream(payload: PlanIn):
    """Variante en streaming SSE de POST /plan (chantier "temps de
    traitement des générations", §2a) -- même principe que
    /conclusions/stream : le plan est émis dès qu'il est prêt, la
    vérification arrive ensuite dans un évènement séparé."""
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        raise HTTPException(status_code=400, detail="Le streaming n'est pas disponible en mode démo -- utilisez /api/analyse/plan.")

    def event_stream():
        trace: list[quality_pipeline.EtapeTrace] = []
        try:
            contexte = construire_contexte_dossier(dossier)

            t0 = time.monotonic()
            yield sse_event("etape", {"etape": "garde_fou", "libelle": "Vérification de la demande"})
            garde = quality_pipeline.executer_garde_fou(contexte)
            trace.append(quality_pipeline.EtapeTrace("garde_fou_entree", "ok", _duree_ms(t0), garde.get("reason", "")))

            t0 = time.monotonic()
            yield sse_event("etape", {"etape": "analyse", "libelle": "Construction du plan de plaidoirie"})
            resultat_principal = legacy_analyse.generer_plan_plaidoirie(contexte, payload.temps_minutes)
            trace.append(quality_pipeline.EtapeTrace("agent_principal", "ok", _duree_ms(t0)))

            strategie_combative = _strategie_combative_si_pertinente(dossier, contexte)
            sections = structurer_sortie_strategique({**resultat_principal}, dossier, "plan", strategie_combative=strategie_combative)
            yield sse_event("principal", {**sections, "statut": "Brouillon"})

            yield sse_event("etape", {"etape": "verification", "libelle": "Vérification des sources et critique"})
            verification, trace_trio = quality_pipeline.executer_trio_qualite(
                quality_pipeline.texte_pour_verification(resultat_principal), [contexte], contexte
            )
            trace.extend(trace_trio)
            yield sse_event("verification", {"verification": verification})

            document = db.creer_document_genere(
                payload.dossier_id, "plan", f"Plan de plaidoirie — {dossier['nom']}", {"temps_minutes": payload.temps_minutes},
                {**sections, "verification": verification}, langue=legacy_analyse.langue_requete(),
            )
            yield sse_event("document", {"document_id": document["id"], "statut": document["statut"]})

            quality_pipeline.log_trace("plan (stream)", trace)
            yield sse_event("done", {})
        except quality_pipeline.DemandeRefusee as e:
            yield sse_event("error", {"detail": e.reason, "risk_level": e.risk_level})
        except Exception as e:
            yield sse_event("error", {"detail": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/simulateur", response_model=SimulateurOut)
def simuler_objections(payload: SimulateurIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        resultat = structurer_sortie_strategique(demo_data.SIMULATEUR_DEMO, dossier, "simulateur")
    else:
        contexte = construire_contexte_dossier(dossier)
        pipeline = quality_pipeline.executer_pipeline_complet(
            feature="simulateur",
            texte_a_screener=contexte,
            fonction_principale=lambda: legacy_analyse.simuler_objections(contexte),
            sources_textes=[contexte],
            contexte_dossier=contexte,
        )
        strategie_combative = _strategie_combative_si_pertinente(dossier, contexte)
        resultat = structurer_sortie_strategique(
            {**pipeline.resultat_principal, "verification": pipeline.verification}, dossier, "simulateur", strategie_combative=strategie_combative
        )
    document = db.creer_document_genere(
        payload.dossier_id, "simulateur", f"Simulateur d'objections — {dossier['nom']}", {}, resultat,
        langue=legacy_analyse.langue_requete(),
    )
    return SimulateurOut(**resultat, document_id=document["id"], statut=document["statut"])


@router.post("/simulateur/export")
def exporter_simulateur(payload: ExportSimulateurIn):
    """Export Word générique (export.py::exporter_texte_libre_word) --
    seule fonctionnalité de l'Arsenal qui n'avait pas d'export, alors que
    Plan et Rapport complet en ont un (voir AUDIT_IMPORT_EXPORT.md)."""
    dossier = get_dossier_or_404(payload.dossier_id)
    lignes = []
    for i, obj in enumerate(payload.objections, start=1):
        lignes.append(f"{i}. [{obj.origine}] {obj.question}")
        if obj.piege:
            lignes.append(f"   Piège : {obj.piege}")
        if obj.piste_reponse:
            lignes.append(f"   Piste de réponse : {obj.piste_reponse}")
        lignes.append("")
    if payload.point_le_plus_faible:
        lignes.append(f"Point le plus faible du dossier : {payload.point_le_plus_faible}")
    texte = "\n".join(lignes)

    chemin = legacy_export.exporter_texte_libre_word(f"{dossier['nom']} — Simulation d'objections", texte)
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/rapport-complet", response_model=RapportCompletOut)
def rapport_complet(payload: RapportCompletIn):
    # Volontairement SANS le pipeline qualité ici : ce endpoint génère déjà
    # jusqu'à 2 analyses en parallèle (plan + simulateur) ; y ajouter le trio
    # qualité pour chacune multiplierait par ~4 le nombre d'appels Claude
    # d'une seule requête HTTP (jusqu'à 8-10 appels), au risque de délais
    # inacceptables -- contraire à la consigne "éviter les appels inutiles,
    # les coûts" (§9). Pour un contrôle qualité complet sur le plan ou le
    # simulateur d'un dossier, utiliser les endpoints /plan et /simulateur
    # dédiés (pipeline complet), qui restent utilisables séparément.
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
    # Profondeur adaptative (§2d du chantier "temps de traitement") :
    # reformulation/analyse dérivée d'un texte déjà fourni -- garde-fou
    # seul, pas le trio qualité complet (disproportionné pour ce type
    # d'analyse, voir /api/chat/contextuel qui applique le même principe).
    quality_pipeline.executer_garde_fou(payload.texte)
    return legacy_analyse.analyser_style_adverse(payload.texte)


@router.post("/traduire", response_model=TraductionOut)
def traduire(payload: TraductionIn):
    demo.exiger_cle_api()
    quality_pipeline.executer_garde_fou(payload.texte)
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
