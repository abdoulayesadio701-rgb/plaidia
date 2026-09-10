"""
/api/dossiers — CRUD des dossiers, recherche transversale, import de
documents (upload multipart) et export Word des faits bruts.

Toute la logique métier vient telle quelle de db.py et export.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import os

import db
import export as legacy_export
from app.deps import extraire_texte_upload, get_dossier_or_404
from app.schemas.dossiers import (
    DossierCreate,
    DossierDomaineUpdate,
    DossierOut,
    DocumentImporteOut,
    FaitsAjout,
    AnalyseHistoriqueOut,
)
from app.schemas.documents import DocumentGenereOut, DocumentStatutIn, DocumentStatutOut
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/dossiers", tags=["dossiers"])


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


@router.get("/{dossier_id}/documents-generes", response_model=list[DocumentGenereOut])
def lister_documents_generes(dossier_id: int, feature: str | None = Query(None)):
    get_dossier_or_404(dossier_id)
    return db.lister_documents_generes(dossier_id, feature)


@router.get("/{dossier_id}/documents-generes/{document_id}", response_model=DocumentGenereOut)
def obtenir_document_genere(dossier_id: int, document_id: int):
    get_dossier_or_404(dossier_id)
    document = db.get_document_genere(document_id)
    if not document or document["dossier_id"] != dossier_id:
        raise HTTPException(status_code=404, detail=f"Document {document_id} introuvable dans ce dossier.")
    return document


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

    texte_extrait = await extraire_texte_upload(fichier)

    db.ajouter_aux_faits(dossier_id, texte_extrait, source=fichier.filename or "document importé")

    return DocumentImporteOut(
        nom_fichier=fichier.filename or "document",
        texte_extrait=texte_extrait,
        caracteres_extraits=len(texte_extrait),
    )


@router.post("/extraire", response_model=DocumentImporteOut, status_code=201)
async def extraire_fichier_sans_dossier(fichier: UploadFile = File(...)):
    """Même extraction que POST /{dossier_id}/documents, mais SANS
    rattachement à un dossier -- pour les pages volontairement
    indépendantes de tout dossier (PV d'audience, contrôle de cohérence :
    voir leurs en-têtes respectifs). N'écrit rien en base ; le texte extrait
    est retourné tel quel, à l'appelant de décider quoi en faire."""
    texte_extrait = await extraire_texte_upload(fichier)

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
