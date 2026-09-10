"""
/api/jurisprudence — Consultation de jurisprudence (Légifrance/Judilibre en
direct ou corpus multi-source validé), collecte Judilibre, validation
manuelle, corpus multi-source (OHADA, UE...), et juridiction active.

Toute la logique métier vient telle quelle de analyse.py, db.py,
recherche_juridique.py et judilibre.py. L'orchestration de /consulter
reproduit fidèlement PlaidIAApp._action_consulter_jurisprudence (gui.py).
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import analyse as legacy_analyse
import db
import judilibre as legacy_judilibre
import recherche_juridique as legacy_rj
from app import demo, quality_pipeline
from app.deps import extraire_texte_upload
from app.schemas.jurisprudence import (
    CollecterIn,
    CollecterOut,
    ConsulterIn,
    ConsulterOut,
    CorpusImportIn,
    CorpusOut,
    JuridictionActiveIn,
    JuridictionActiveOut,
    JurisprudenceOut,
    ValiderCorpusSourceIn,
    ValiderCorpusSourceOut,
)
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(prefix="/api/jurisprudence", tags=["jurisprudence"])

JURIDICTION_PAR_DEFAUT = "Légifrance (France)"


@router.post("/consulter", response_model=ConsulterOut)
def consulter(payload: ConsulterIn):
    demo.exiger_cle_api()
    dossier = db.get_dossier(payload.dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Dossier {payload.dossier_id} introuvable.")
    notions = legacy_analyse.identifier_notions_juridiques(payload.question, payload.but)
    mots_cles = notions.get("mots_cles_recherche") or []
    requete_recherche = " ".join(mots_cles) if mots_cles else payload.question

    if payload.source == JURIDICTION_PAR_DEFAUT:
        contexte_live = legacy_rj.rechercher_contexte_juridique(requete_recherche)
        contexte_recherche = legacy_rj.formater_contexte_pour_prompt(contexte_live)
    else:
        textes = db.get_corpus_valide(source=payload.source)
        if textes:
            bloc = "\n".join(f"[{t['reference'] or 'sans référence'}] {t['contenu'][:2000]}" for t in textes)
            contexte_recherche = f"--- Source : {payload.source} ---\n{bloc}"
        else:
            contexte_recherche = ""

    # Pipeline complet (§9 ARCHITECTURE_MULTI_AGENTS.md) : c'est ici que le
    # contrôle déterministe des citations est le plus fort -- contexte_recherche
    # contient les références réellement retrouvées (Légifrance/Judilibre en
    # direct, ou corpus validé), donc chaque décision citée dans la réponse
    # peut être confrontée à une source concrète, pas seulement au texte brut.
    pipeline = quality_pipeline.executer_pipeline_complet(
        feature="jurisprudence_consultation",
        texte_a_screener=payload.question,
        fonction_principale=lambda: legacy_analyse.consulter_jurisprudence(
            payload.question,
            contexte_recherche,
            qualification=notions.get("qualification_juridique", ""),
            but=notions.get("but", payload.but),
        ),
        sources_textes=[contexte_recherche] if contexte_recherche else [],
    )
    resultat = {"notions": notions, "reponse": pipeline.resultat_principal, "verification": pipeline.verification}
    document = db.creer_document_genere(
        payload.dossier_id,
        "jurisprudence_consultation",
        f"Consultation — {payload.question[:60]}",
        {"question": payload.question, "but": payload.but, "source": payload.source},
        resultat,
    )
    return ConsulterOut(**resultat, document_id=document["id"], statut=document["statut"])


@router.post("/collecter", response_model=CollecterOut)
def collecter(payload: CollecterIn):
    """Interroge Judilibre puis insère chaque décision en base, NON validée
    — exactement comme _action_collecter_jurisprudence : rien n'est
    utilisable en citation tant qu'un humain ne l'a pas validée."""
    collectees = legacy_judilibre.collecter_jurisprudence(
        query=payload.query, domaine=payload.domaine, max_results=10
    )
    for c in collectees:
        db.add_jurisprudence(
            reference=c["reference"], resume=c["resume"], domaine=c["domaine"], source=c["source"], validee=False
        )
    return CollecterOut(decisions=collectees, nombre_collecte=len(collectees))


@router.get("/en-attente", response_model=list[JurisprudenceOut])
def jurisprudence_en_attente(domaine: str | None = None):
    return db.get_jurisprudence_en_attente(domaine)


@router.get("/validee", response_model=list[JurisprudenceOut])
def jurisprudence_validee(domaine: str | None = None):
    return db.get_jurisprudence_validee(domaine)


@router.post("/{jurisprudence_id}/valider", status_code=204)
def valider_jurisprudence(jurisprudence_id: int):
    db.valider_jurisprudence(jurisprudence_id)


@router.delete("/{jurisprudence_id}", status_code=204)
def rejeter_jurisprudence(jurisprudence_id: int):
    """Supprime une référence en attente non pertinente (ne touche jamais
    une référence déjà validée — comportement hérité de db.py)."""
    db.rejeter_jurisprudence(jurisprudence_id)


# --- Corpus multi-source (OHADA, UE, droit sénégalais...) -----------------

@router.post("/corpus", response_model=CorpusOut, status_code=201)
def importer_texte_corpus(payload: CorpusImportIn):
    texte_id = db.ajouter_texte_corpus(
        source=payload.source,
        contenu=payload.contenu,
        pays=payload.pays,
        type_texte=payload.type_texte,
        domaine=payload.domaine,
        reference=payload.reference,
        date_texte=payload.date_texte,
        validee=False,
    )
    textes = db.get_corpus_en_attente()
    trouve = next((t for t in textes if t["id"] == texte_id), None)
    if not trouve:
        raise HTTPException(status_code=500, detail="Le texte importé n'a pas pu être relu après insertion.")
    return trouve


@router.post("/corpus/importer-fichier", response_model=CorpusOut, status_code=201)
async def importer_fichier_corpus(
    source: str = Form(..., description="Ex. OHADA, Union européenne, Droit sénégalais..."),
    pays: str = Form(""),
    type_texte: str = Form(""),
    domaine: str = Form(""),
    reference: str = Form(""),
    date_texte: str = Form(""),
    fichier: UploadFile = File(...),
):
    """Même import que POST /corpus, mais à partir d'un fichier (PDF, DOCX,
    TXT...) plutôt que d'un texte collé -- les textes de corpus (actes
    OHADA, textes de l'UE...) sont typiquement de longs documents déjà
    disponibles sous cette forme (voir AUDIT_IMPORT_EXPORT.md). Réutilise
    extraire_texte_upload (app.deps), le même point d'entrée que l'import
    de documents de dossier -- aucune logique d'extraction dupliquée."""
    texte_extrait = await extraire_texte_upload(fichier)
    texte_id = db.ajouter_texte_corpus(
        source=source,
        contenu=texte_extrait,
        pays=pays,
        type_texte=type_texte,
        domaine=domaine,
        reference=reference or (fichier.filename or ""),
        date_texte=date_texte,
        validee=False,
    )
    textes = db.get_corpus_en_attente()
    trouve = next((t for t in textes if t["id"] == texte_id), None)
    if not trouve:
        raise HTTPException(status_code=500, detail="Le texte importé n'a pas pu être relu après insertion.")
    return trouve


@router.get("/corpus/en-attente", response_model=list[CorpusOut])
def corpus_en_attente():
    return db.get_corpus_en_attente()


@router.get("/corpus/valide", response_model=list[CorpusOut])
def corpus_valide(source: str | None = None, pays: str | None = None, domaine: str | None = None):
    return db.get_corpus_valide(source=source, pays=pays, domaine=domaine)


@router.get("/corpus/sources", response_model=list[str])
def sources_corpus():
    """Sources déjà présentes dans le corpus — utilisé pour peupler le
    sélecteur de juridiction, en plus de « Légifrance (France) »."""
    sources = db.lister_sources_corpus()
    return [JURIDICTION_PAR_DEFAUT] + [s for s in sources if s != JURIDICTION_PAR_DEFAUT]


@router.post("/corpus/{texte_id}/valider", status_code=204)
def valider_corpus(texte_id: int):
    db.valider_texte_corpus(texte_id)


@router.post("/corpus/valider-source", response_model=ValiderCorpusSourceOut)
def valider_corpus_source(payload: ValiderCorpusSourceIn):
    """Valide en un seul geste tous les textes en attente d'une même
    source (voir db.py::valider_texte_corpus_par_source) -- pour les
    imports en masse (dataset structuré) où une validation article par
    article est irréaliste. Si `domaine` est fourni, restreint la
    validation à ce sous-ensemble (utile quand un import contient des lots
    de qualité inégale). Ne touche jamais les textes déjà validés ni ceux
    d'une autre source/domaine."""
    nombre = db.valider_texte_corpus_par_source(payload.source, domaine=payload.domaine or None)
    return ValiderCorpusSourceOut(source=payload.source, domaine=payload.domaine, nombre_valide=nombre)


@router.delete("/corpus/{texte_id}", status_code=204)
def rejeter_corpus(texte_id: int):
    db.rejeter_texte_corpus(texte_id)


# --- Juridiction active (réglage persistant) -------------------------------

@router.get("/juridiction-active", response_model=JuridictionActiveOut)
def obtenir_juridiction_active():
    return JuridictionActiveOut(juridiction=db.get_parametre("juridiction_active", JURIDICTION_PAR_DEFAUT))


@router.put("/juridiction-active", response_model=JuridictionActiveOut)
def definir_juridiction_active(payload: JuridictionActiveIn):
    db.set_parametre("juridiction_active", payload.juridiction)
    return JuridictionActiveOut(juridiction=payload.juridiction)
