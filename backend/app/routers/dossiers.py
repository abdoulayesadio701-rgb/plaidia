"""
/api/dossiers — CRUD des dossiers, recherche transversale, import de
documents (upload multipart) et export Word des faits bruts.

Toute la logique métier vient telle quelle de db.py et export.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import os
import tempfile
from pathlib import Path

import db
import export as legacy_export
import extract as legacy_extract
from app.deps import get_dossier_or_404
from app.schemas.dossiers import (
    DossierCreate,
    DossierDomaineUpdate,
    DossierOut,
    DocumentImporteOut,
    FaitsAjout,
    AnalyseHistoriqueOut,
)
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/dossiers", tags=["dossiers"])

EXTENSIONS_AUTORISEES = {".pdf", ".docx", ".xlsx", ".xls", ".txt", ".png", ".jpg", ".jpeg", ".webp"}


@router.post("/", response_model=DossierOut, status_code=201)
def creer_dossier(payload: DossierCreate):
    dossier_id = db.create_dossier(
        nom=payload.nom,
        domaine=payload.domaine,
        parties=payload.parties,
        faits=payload.faits,
        numero_dossier=payload.numero_dossier,
    )
    return get_dossier_or_404(dossier_id)


@router.get("/", response_model=list[DossierOut])
def lister_dossiers():
    return [dict(r) for r in db.list_dossiers()]


@router.get("/recherche", response_model=list[dict])
def rechercher_dossiers(terme: str):
    """Recherche un mot-clé dans les faits, parties, nom, domaine et
    analyses de tous les dossiers."""
    return db.rechercher_dans_dossiers(terme)


@router.get("/{dossier_id}", response_model=DossierOut)
def obtenir_dossier(dossier_id: int):
    return get_dossier_or_404(dossier_id)


@router.patch("/{dossier_id}/domaine", response_model=DossierOut)
def modifier_domaine(dossier_id: int, payload: DossierDomaineUpdate):
    get_dossier_or_404(dossier_id)  # 404 propre si le dossier n'existe pas
    db.update_domaine(dossier_id, payload.domaine)
    return get_dossier_or_404(dossier_id)


@router.delete("/{dossier_id}", status_code=204)
def supprimer_dossier(dossier_id: int):
    get_dossier_or_404(dossier_id)
    db.delete_dossier(dossier_id)


@router.get("/{dossier_id}/analyses", response_model=list[AnalyseHistoriqueOut])
def historique_analyses(dossier_id: int):
    get_dossier_or_404(dossier_id)
    return db.get_analyses_for_dossier(dossier_id)


@router.post("/{dossier_id}/faits", status_code=201)
def ajouter_texte_aux_faits(dossier_id: int, payload: FaitsAjout):
    """Ajoute un texte collé directement (alternative à l'upload de fichier)
    aux faits accumulés du dossier — équivalent du choix « Non, transmettre
    le texte directement » dans « Préparer ce dossier » côté tkinter."""
    get_dossier_or_404(dossier_id)
    db.ajouter_aux_faits(dossier_id, payload.texte, source=payload.source)
    return {"detail": "Texte ajouté aux faits du dossier."}


@router.post("/{dossier_id}/documents", response_model=DocumentImporteOut, status_code=201)
async def importer_document(dossier_id: int, fichier: UploadFile = File(...)):
    """Upload multipart d'un document (PDF/DOCX/XLSX/TXT/image) : le texte
    est extrait via extract.extract_text() puis ajouté aux faits du dossier,
    exactement comme le flux « Préparer ce dossier » de gui.py."""
    get_dossier_or_404(dossier_id)

    suffix = Path(fichier.filename or "").suffix.lower()
    if suffix not in EXTENSIONS_AUTORISEES:
        raise HTTPException(
            status_code=415,
            detail=f"Format non supporté : {suffix or '(aucun)'}. Formats acceptés : {legacy_extract.FORMATS_SUPPORTES}",
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await fichier.read())
            tmp_path = tmp.name

        texte_extrait = legacy_extract.extract_text(tmp_path)
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    db.ajouter_aux_faits(dossier_id, texte_extrait, source=fichier.filename or "document importé")

    return DocumentImporteOut(
        nom_fichier=fichier.filename or "document",
        texte_extrait=texte_extrait,
        caracteres_extraits=len(texte_extrait),
    )


@router.get("/{dossier_id}/export/faits-bruts")
def exporter_faits_bruts(dossier_id: int):
    dossier = get_dossier_or_404(dossier_id)
    chemin = legacy_export.exporter_faits_bruts_word(dossier)
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
