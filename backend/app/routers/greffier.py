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
from app import delais, demo, demo_data, demo_data_outils, quality_pipeline
from app.deps import construire_contexte_dossier, get_dossier_or_404
from app.security_guard import executer_garde_fou
from app.schemas.greffier import (
    CatalogueDelaiOut,
    ChronologieIn,
    ChronologieOut,
    ClassementIn,
    ClassementOut,
    CoherenceIn,
    CoherenceOut,
    DelaisIn,
    DelaisOut,
    ExportChronologieIn,
    ExportCoherenceIn,
    ExportDelaisIn,
    ExportExtractionIn,
    ExportRapportInstructionIn,
    ExportRequisitoireIn,
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
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/greffier", tags=["greffier"])


@router.post("/chronologie", response_model=ChronologieOut)
def chronologie(payload: ChronologieIn):
    """Route vers DeepSeek (voir analyse.TypeTache.STRUCTURATION) -- garde-fou
    d'entrée ajouté ici en même temps que le changement de fournisseur : il
    manquait déjà sous Claude sur cette route.

    Persistée dans documents_generes (feature="chronologie"), même
    mécanisme que /plan et /simulateur -- y compris en mode démo -- pour
    qu'elle survive à une navigation ou un refresh (voir ChronologiePage
    côté front)."""
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        resultat = demo_data.chronologie_demo()
    else:
        demo.exiger_cle_api_deepseek()
        contexte = construire_contexte_dossier(dossier)
        executer_garde_fou(contexte)
        resultat = legacy_analyse.construire_chronologie(contexte)
    document = db.creer_document_genere(
        payload.dossier_id, "chronologie", f"Chronologie — {dossier['nom']}", {}, resultat,
    )
    return ChronologieOut(**resultat, document_id=document["id"], statut=document["statut"])


@router.post("/chronologie/export")
def exporter_chronologie(payload: ExportChronologieIn):
    """Export Word générique (export.py::exporter_texte_libre_word) --
    seuls les formats Word/PDF sont acceptés en export dans l'application
    (voir AUDIT_IMPORT_EXPORT.md), le CSV a été retiré."""
    dossier = get_dossier_or_404(payload.dossier_id)
    lignes = [f"{e.date} — {e.evenement}" for e in payload.evenements]
    chemin = legacy_export.exporter_texte_libre_word(
        f"{dossier['nom']} — Chronologie", "\n".join(lignes)
    )
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/extraction", response_model=ExtractionOut)
def extraction(payload: ExtractionIn):
    """Route vers DeepSeek (voir analyse.TypeTache.EXTRACTION) -- garde-fou
    d'entrée et contrôle déterministe des citations ajoutés ici en même
    temps que le changement de fournisseur : ils manquaient déjà sous
    Claude sur cette route (contrairement à /api/analyse/conclusions), ce
    n'est pas spécifique à DeepSeek."""
    if demo.mode_demo_effectif():
        return demo_data_outils.extraction_demo(payload.texte)
    demo.exiger_cle_api_deepseek()
    executer_garde_fou(payload.texte)
    elements = legacy_analyse.extraire_elements_cles(payload.texte)
    for ref in elements.get("references", []):
        citations = quality_pipeline.verifier_citations_deterministe(str(ref), [payload.texte])
        for c in citations:
            if c["statut_deterministe"] != "VERIFIE":
                print(f"[greffier] citation non vérifiée dans une extraction DeepSeek : {c}", flush=True)
    return elements


@router.post("/extraction/export")
def exporter_extraction(payload: ExportExtractionIn):
    """Export Word générique, sans dossier requis -- même principe que
    /pv-audience/export."""
    blocs = [
        ("DATES", payload.dates),
        ("PERSONNES ET PARTIES", payload.personnes_et_parties),
        ("RÉFÉRENCES", payload.references),
        ("DEMANDES", payload.demandes),
        ("DÉCISIONS", payload.decisions),
    ]
    lignes = []
    for titre_bloc, elements in blocs:
        lignes.append(titre_bloc)
        if not elements:
            lignes.append("— Rien détecté")
        for e in elements:
            lignes.append(f"- {e}")
        lignes.append("")

    chemin = legacy_export.exporter_texte_libre_word("Extraction d'éléments clés", "\n".join(lignes))
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/classement", response_model=ClassementOut)
def classement(payload: ClassementIn):
    if demo.mode_demo_effectif():
        return demo_data_outils.classement_demo(payload.texte)
    return legacy_analyse.classifier_document(payload.texte)


@router.post("/coherence", response_model=CoherenceOut)
def controle_coherence(payload: CoherenceIn):
    """Extrait d'abord les éléments clés de chaque document (mêmes règles
    que /extraction), puis les compare — reproduit exactement le flux de
    PlaidIAApp._action_controle_coherence (gui.py)."""
    if demo.mode_demo_effectif():
        return CoherenceOut(**demo_data_outils.coherence_demo([(d.nom_document, d.texte) for d in payload.documents]))
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


@router.post("/coherence/export")
def exporter_coherence(payload: ExportCoherenceIn):
    """Export Word générique, sans dossier requis -- même principe que
    /pv-audience/export."""
    lignes = ["CONTRADICTIONS RELEVÉES"]
    if not payload.contradictions:
        lignes.append("— Aucune contradiction relevée")
    for c in payload.contradictions:
        lignes.append(f"[{c.gravite}] {c.sujet}")
        lignes.append(f"  Document 1 : {c.document_1}")
        lignes.append(f"  Document 2 : {c.document_2}")
    lignes.append("")

    if payload.elements_coherents:
        lignes.append("ÉLÉMENTS COHÉRENTS")
        for e in payload.elements_coherents:
            lignes.append(f"- {e}")
        lignes.append("")

    if payload.limites_analyse:
        lignes.append("LIMITES DE L'ANALYSE")
        lignes.append(payload.limites_analyse)

    chemin = legacy_export.exporter_texte_libre_word("Contrôle de cohérence entre documents", "\n".join(lignes))
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/recherche", response_model=list[dict])
def recherche_transversale(terme: str):
    return db.rechercher_dans_dossiers(terme)


@router.post("/pv-audience", response_model=PvAudienceOut)
def pv_audience(payload: PvAudienceIn):
    """Route vers DeepSeek (voir analyse.TypeTache.STRUCTURATION) -- garde-fou
    d'entrée et contrôle déterministe des citations ajoutés ici en même
    temps que le changement de fournisseur : ils manquaient déjà sous
    Claude sur cette route."""
    if demo.mode_demo_effectif():
        return PvAudienceOut(texte=demo_data_outils.pv_audience_demo(payload.notes))
    demo.exiger_cle_api_deepseek()
    executer_garde_fou(payload.notes)
    texte = legacy_analyse.rediger_pv(payload.notes)
    for c in quality_pipeline.verifier_citations_deterministe(texte, [payload.notes]):
        if c["statut_deterministe"] != "VERIFIE":
            print(f"[greffier] citation non vérifiée dans un PV DeepSeek : {c}", flush=True)
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
    """Persistée dans documents_generes (feature="verification_procedurale"),
    même mécanisme que /plan et /simulateur -- pour qu'elle survive à une
    navigation ou un refresh (voir VerificationProceduralePage côté front)."""
    dossier = get_dossier_or_404(payload.dossier_id)
    if demo.mode_demo_effectif():
        resultat = demo_data_outils.verification_procedurale_demo()
    else:
        contexte = construire_contexte_dossier(dossier)
        resultat = legacy_analyse.verifier_procedure(contexte)
    document = db.creer_document_genere(
        payload.dossier_id, "verification_procedurale", f"Vérification procédurale — {dossier['nom']}", {}, resultat,
    )
    return VerificationProceduraleOut(**resultat, document_id=document["id"], statut=document["statut"])


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


@router.get("/delais/catalogue", response_model=list[CatalogueDelaiOut])
def catalogue_delais():
    return [
        CatalogueDelaiOut(
            code=r.code, libelle=r.libelle, duree=delais.duree_texte(r), reference=r.reference,
            point_de_depart=r.point_de_depart,
        )
        for r in delais.CATALOGUE.values()
    ]


@router.post("/delais", response_model=DelaisOut)
def calculer_delais(payload: DelaisIn):
    """Calcul déterministe (voir app/delais.py, aucun appel modèle : fonctionne
    identiquement en mode démo) puis persistance dans documents_generes
    (feature="delais"), même mécanisme que /chronologie -- pour que les
    échéances survivent à une navigation ou un refresh."""
    dossier = get_dossier_or_404(payload.dossier_id)
    calcules = []
    for demande in payload.delais:
        regle = delais.CATALOGUE.get(demande.type)
        if regle is None:
            raise HTTPException(status_code=422, detail=f"Type de délai inconnu : {demande.type}")
        brute, effective = delais.calculer_echeance(regle, demande.date_depart)
        calcules.append({
            "type": regle.code,
            "libelle": regle.libelle,
            "reference": regle.reference,
            "duree": delais.duree_texte(regle),
            "point_de_depart": regle.point_de_depart,
            "date_depart": demande.date_depart.isoformat(),
            "echeance_brute": brute.isoformat(),
            "date_echeance": effective.isoformat(),
            "proroge": effective != brute,
            "precision": demande.libelle,
        })
    resultat = {"delais": calcules, "avertissement": delais.AVERTISSEMENT}
    document = db.creer_document_genere(
        payload.dossier_id, "delais", f"Délais de procédure — {dossier['nom']}", {}, resultat,
    )
    return DelaisOut(**resultat, document_id=document["id"], statut=document["statut"])


@router.post("/delais/export")
def exporter_delais(payload: ExportDelaisIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    lignes = []
    for d in sorted(payload.delais, key=lambda d: d.date_echeance):
        intitule = f"{d.libelle} ({d.precision})" if d.precision else d.libelle
        lignes.append(intitule)
        lignes.append(f"  Base légale : {d.reference} — délai de {d.duree}")
        lignes.append(f"  Point de départ : {d.point_de_depart} du {d.date_depart}")
        ligne_echeance = f"  Échéance : {d.date_echeance}"
        if d.proroge:
            ligne_echeance += f" (prorogée depuis le {d.echeance_brute}, art. 642 CPC)"
        lignes.append(ligne_echeance)
        lignes.append("")

    chemin = legacy_export.exporter_texte_libre_word(
        f"{dossier['nom']} — Délais de procédure",
        "\n".join(lignes),
        note_bas_page=payload.avertissement or delais.AVERTISSEMENT,
    )
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/requisitoire", response_model=RequisitoireOut)
def requisitoire(payload: RequisitoireIn):
    """Route vers DeepSeek (voir analyse.TypeTache.STRUCTURATION) -- garde-fou
    d'entrée et contrôle déterministe des citations ajoutés ici en même
    temps que le changement de fournisseur : ils manquaient déjà sous
    Claude sur cette route."""
    if demo.mode_demo_effectif():
        return demo_data_outils.requisitoire_demo()
    demo.exiger_cle_api_deepseek()
    executer_garde_fou(payload.texte)
    resultat = legacy_analyse.analyser_requisitoire(payload.texte)
    for point in resultat.get("points_attention", []):
        for c in quality_pipeline.verifier_citations_deterministe(str(point), [payload.texte]):
            if c["statut_deterministe"] != "VERIFIE":
                print(f"[greffier] citation non vérifiée dans un réquisitoire DeepSeek : {c}", flush=True)
    return resultat


@router.post("/rapport-instruction", response_model=RapportInstructionOut)
def rapport_instruction(payload: RapportInstructionIn):
    """Route vers DeepSeek (voir analyse.TypeTache.STRUCTURATION) -- garde-fou
    d'entrée et contrôle déterministe des citations ajoutés ici en même
    temps que le changement de fournisseur : ils manquaient déjà sous
    Claude sur cette route."""
    if demo.mode_demo_effectif():
        return demo_data_outils.rapport_instruction_demo()
    demo.exiger_cle_api_deepseek()
    executer_garde_fou(payload.texte)
    resultat = legacy_analyse.analyser_rapport_instruction(payload.texte)
    for point in resultat.get("points_attention", []):
        for c in quality_pipeline.verifier_citations_deterministe(str(point), [payload.texte]):
            if c["statut_deterministe"] != "VERIFIE":
                print(f"[greffier] citation non vérifiée dans un rapport d'instruction DeepSeek : {c}", flush=True)
    return resultat


def _lignes_liste(titre: str, elements: list[str]) -> list[str]:
    lignes = [titre]
    if not elements:
        lignes.append("— Rien détecté")
    lignes.extend(f"- {e}" for e in elements)
    lignes.append("")
    return lignes


def _reponse_word(chemin: str) -> FileResponse:
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/requisitoire/export")
def exporter_requisitoire(payload: ExportRequisitoireIn):
    """Export Word générique, sans dossier requis -- même principe que
    /extraction/export."""
    lignes = ["QUALIFICATION RETENUE", payload.qualification_retenue or "— Non précisée", ""]
    lignes += ["PEINE REQUISE", payload.peine_requise, ""]
    lignes += _lignes_liste("FAITS ET ÉLÉMENTS INVOQUÉS", payload.faits_et_elements_invoques)
    lignes += _lignes_liste("CIRCONSTANCES AGGRAVANTES", payload.circonstances_aggravantes)
    lignes += _lignes_liste("CIRCONSTANCES ATTÉNUANTES", payload.circonstances_attenuantes)
    lignes += _lignes_liste("POINTS D'ATTENTION", payload.points_attention)
    chemin = legacy_export.exporter_texte_libre_word(
        "Analyse d'un réquisitoire",
        "\n".join(lignes),
        note_bas_page="Analyse automatisée à vérifier manuellement -- ne remplace pas le contrôle d'un professionnel du droit.",
    )
    return _reponse_word(chemin)


@router.post("/rapport-instruction/export")
def exporter_rapport_instruction(payload: ExportRapportInstructionIn):
    """Export Word générique, sans dossier requis."""
    lignes = ["SENS PROPOSÉ", payload.sens_propose, ""]
    lignes += _lignes_liste("ACTES D'INSTRUCTION", payload.actes_instruction)
    lignes += _lignes_liste("MESURES ORDONNÉES", payload.mesures_ordonnees)
    lignes += _lignes_liste("ÉLÉMENTS À CHARGE", payload.elements_a_charge)
    lignes += _lignes_liste("ÉLÉMENTS À DÉCHARGE", payload.elements_a_decharge)
    lignes += _lignes_liste("POINTS D'ATTENTION", payload.points_attention)
    chemin = legacy_export.exporter_texte_libre_word(
        "Analyse d'un rapport d'instruction",
        "\n".join(lignes),
        note_bas_page="Analyse automatisée à vérifier manuellement -- ne remplace pas le contrôle d'un professionnel du droit.",
    )
    return _reponse_word(chemin)
