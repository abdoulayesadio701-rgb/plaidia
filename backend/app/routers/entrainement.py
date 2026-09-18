"""
/api/entrainement — bilan d'un entraînement chronométré à la plaidoirie
(voir frontend/src/pages/arsenal/EntrainementPage.tsx : le chronomètre vit
côté navigateur, ce router n'enregistre et n'exporte que le bilan).

Aucun appel modèle : fonctionne à l'identique en mode démo.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import os

import db
import export as legacy_export
from app import entrainement
from app.deps import get_dossier_or_404
from app.schemas.entrainement import BilanOut, EntrainementIn, ExportBilanIn
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/entrainement", tags=["entrainement"])

LIBELLES_STATUT = {
    entrainement.DANS_LES_TEMPS: "dans les temps",
    entrainement.DEPASSE: "dépassée",
    entrainement.EN_AVANCE: "en avance",
    entrainement.NON_TRAITE: "non traitée",
}


@router.post("/", response_model=BilanOut)
def enregistrer_bilan(payload: EntrainementIn):
    """Calcule le bilan puis le persiste dans documents_generes
    (feature="entrainement"), même mécanisme que /chronologie -- pour qu'il
    survive à une navigation ou un refresh."""
    dossier = get_dossier_or_404(payload.dossier_id)
    bilan = entrainement.construire_bilan([s.model_dump() for s in payload.sections])
    document = db.creer_document_genere(
        payload.dossier_id, "entrainement", f"Entraînement — {dossier['nom']}", {}, bilan,
    )
    return BilanOut(**bilan, document_id=document["id"], statut=document["statut"])


@router.post("/export")
def exporter_bilan(payload: ExportBilanIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    lignes = []
    for s in payload.sections:
        lignes.append(s.point)
        if s.statut == entrainement.NON_TRAITE:
            lignes.append(f"  Alloué : {entrainement.formater_duree(s.alloue_secondes)} — non traitée")
        else:
            lignes.append(
                f"  Alloué : {entrainement.formater_duree(s.alloue_secondes)} — "
                f"réel : {entrainement.formater_duree(s.reel_secondes)} — "
                f"écart : {entrainement.formater_duree(s.ecart_secondes)} ({LIBELLES_STATUT.get(s.statut, s.statut)})"
            )
        lignes.append("")
    lignes.append(
        f"TOTAL (sections traitées) — alloué : {entrainement.formater_duree(payload.total_alloue_secondes)}, "
        f"réel : {entrainement.formater_duree(payload.total_reel_secondes)}, "
        f"écart : {entrainement.formater_duree(payload.total_ecart_secondes)}"
    )

    chemin = legacy_export.exporter_texte_libre_word(f"{dossier['nom']} — Bilan d'entraînement", "\n".join(lignes))
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
