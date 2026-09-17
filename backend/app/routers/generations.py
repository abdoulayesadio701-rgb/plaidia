"""
/api/generations — Générations longues (analyse de conclusions, plan de
plaidoirie...) lancées en arrière-plan : la requête HTTP renvoie
immédiatement un id de suivi (202) sans attendre la fin du traitement,
pour que le front puisse naviguer ailleurs pendant qu'un thread serveur
termine le travail -- portage de gui.py::PlaidIAApp._lancer_generation
(desktop Tkinter) vers l'app web, même principe : le dossier et le
contexte de la requête (clé API personnelle, langue) sont figés au
lancement, jamais relus après coup.

Complète /api/analyse (synchrone) et /api/analyse/*/stream (SSE, lié à la
connexion HTTP ouverte) sans les remplacer : ce sont des points d'entrée
supplémentaires, opt-in, qui réutilisent la même logique métier.

Toute la logique métier vient telle quelle de analyse.py et db.py --
db.generations (voir db.py, section "Générations") est la même table que
gui.py utilise déjà pour son propre historique persistant.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import threading

import analyse as legacy_analyse
import db
from app import demo, demo_data, quality_pipeline
from app.deps import construire_contexte_dossier, get_dossier_or_404, structurer_sortie_strategique
from app.routers.analyse import _strategie_combative_si_pertinente
from app.schemas.analyse import ConclusionsIn, PlanIn
from app.schemas.generations import GenerationLanceeOut, GenerationOut
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/generations", tags=["generations"])


def _lancer_arriere_plan(feature: str, dossier_id: int | None, libelle_generation: str, fonction_tache) -> int:
    """Journalise le lancement dans db.generations (statut 'en_cours') puis
    démarre fonction_tache() dans un thread séparé, qui journalise la fin
    (succès ou échec) à son tour -- voir db.creer_generation/
    terminer_generation/echouer_generation, déjà utilisées par gui.py.

    La clé API personnelle et la langue de la requête (voir main.py,
    ContextVar posés par les middlewares) sont capturées ICI, sur le
    thread de la requête, et reposées explicitement au tout début du
    thread : un ContextVar ne traverse PAS automatiquement vers un
    threading.Thread nouvellement créé (contrairement à une tâche asyncio
    dans la même boucle d'évènements) -- sans ce relais explicite, la clé
    personnelle et la langue choisies par le visiteur seraient
    silencieusement perdues dès que la réponse 202 est renvoyée (le
    middleware réinitialise son ContextVar dans son `finally`, qui
    s'exécute AVANT que le thread d'arrière-plan n'ait fini)."""
    generation_id = db.creer_generation(dossier_id, feature, libelle_generation)
    cle_api = legacy_analyse.obtenir_cle_api_requete()
    langue = legacy_analyse.langue_requete()

    def travail():
        legacy_analyse.definir_cle_api_requete(cle_api)
        legacy_analyse.definir_langue_requete(langue)
        try:
            resultat = fonction_tache()
            db.terminer_generation(generation_id, resultat)
        except Exception as e:
            db.echouer_generation(generation_id, str(e))

    threading.Thread(target=travail, daemon=True).start()
    return generation_id


@router.post("/conclusions", status_code=202, response_model=GenerationLanceeOut)
def lancer_conclusions(payload: ConclusionsIn):
    """Variante en arrière-plan de POST /api/analyse/conclusions -- même
    pipeline complet (garde-fou -> agent principal -> trio qualité), mais
    exécutée après que la réponse 202 est renvoyée."""
    dossier = get_dossier_or_404(payload.dossier_id) if payload.dossier_id is not None else None
    mode_demo = demo.mode_demo_effectif()

    def tache():
        if mode_demo:
            resultat = demo_data.conclusions_demo()
            sections = structurer_sortie_strategique(resultat, dossier or {"id": 0, "nom": "", "faits": "", "parties": ""}, "conclusions")
            return {
                "arguments": sections["arguments"], "points_attention": sections["points_attention"],
                "diagnostic": sections["diagnostic"], "strategie": sections["strategie"], "analyse_id": None,
            }

        contexte_dossier = construire_contexte_dossier(dossier) if dossier else ""
        pipeline = quality_pipeline.executer_pipeline_complet(
            feature="conclusions",
            texte_a_screener=payload.texte,
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
        return {
            "arguments": resultat.get("arguments", []), "points_attention": resultat.get("points_attention", []),
            "analyse_id": analyse_id, "verification": pipeline.verification,
            "diagnostic": sections["diagnostic"], "strategie": sections["strategie"],
        }

    libelle_generation = f"Analyse des conclusions adverses — {dossier['nom']}" if dossier else "Analyse des conclusions adverses"
    generation_id = _lancer_arriere_plan("conclusions", payload.dossier_id, libelle_generation, tache)
    return GenerationLanceeOut(id=generation_id)


@router.post("/plan", status_code=202, response_model=GenerationLanceeOut)
def lancer_plan(payload: PlanIn):
    """Variante en arrière-plan de POST /api/analyse/plan."""
    dossier = get_dossier_or_404(payload.dossier_id)
    mode_demo = demo.mode_demo_effectif()

    def tache():
        if mode_demo:
            resultat = structurer_sortie_strategique(demo_data.plan_demo(), dossier, "plan")
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
        return {**resultat, "document_id": document["id"], "statut": document["statut"]}

    generation_id = _lancer_arriere_plan("plan", payload.dossier_id, f"Plan de plaidoirie — {dossier['nom']}", tache)
    return GenerationLanceeOut(id=generation_id)


@router.get("/", response_model=list[GenerationOut])
def lister_generations(dossier_id: int | None = None):
    return db.list_generations(dossier_id=dossier_id)


@router.get("/{generation_id}", response_model=GenerationOut)
def obtenir_generation(generation_id: int):
    generation = db.get_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail="Génération introuvable.")
    return generation


@router.delete("/{generation_id}", status_code=204)
def supprimer_generation(generation_id: int):
    """Suppression DÉFINITIVE, sur action explicite uniquement (bouton
    « Supprimer » confirmé côté front) -- jamais appelée automatiquement,
    aucune expiration. Voir db.supprimer_generation."""
    db.supprimer_generation(generation_id)
