"""API commune des documents générés persistés."""

from app.bootstrap import ROOT_DIR  # noqa: F401

import db
from app.deps import libelle
from app.schemas.documents import DocumentGenereOut, DocumentStatutIn
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/documents-generes", tags=["documents-generes"])


@router.get("/{document_id}", response_model=DocumentGenereOut)
def obtenir_document(document_id: int):
    document = db.get_document_genere(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=libelle("document_introuvable", document_id=document_id))
    return document


@router.patch("/{document_id}/statut", response_model=DocumentGenereOut)
def changer_statut(document_id: int, payload: DocumentStatutIn):
    try:
        document = db.changer_statut_document(document_id, payload.statut)
    except db.TransitionStatutInvalide as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    if not document:
        raise HTTPException(status_code=404, detail=libelle("document_introuvable", document_id=document_id))
    return document


@router.delete("/{document_id}", status_code=204)
def supprimer_document(document_id: int):
    """Suppression DÉFINITIVE, sur action explicite uniquement (bouton
    « Supprimer » confirmé côté front) -- jamais appelée automatiquement,
    aucune expiration. Voir db.supprimer_document_genere."""
    if not db.get_document_genere(document_id):
        raise HTTPException(status_code=404, detail=libelle("document_introuvable", document_id=document_id))
    db.supprimer_document_genere(document_id)
