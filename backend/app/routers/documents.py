"""API commune des documents générés persistés."""

from app.bootstrap import ROOT_DIR  # noqa: F401

import db
from app.schemas.documents import DocumentGenereOut, DocumentStatutIn
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/documents-generes", tags=["documents-generes"])


@router.get("/{document_id}", response_model=DocumentGenereOut)
def obtenir_document(document_id: int):
    document = db.get_document_genere(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} introuvable.")
    return document


@router.patch("/{document_id}/statut", response_model=DocumentGenereOut)
def changer_statut(document_id: int, payload: DocumentStatutIn):
    try:
        document = db.changer_statut_document(document_id, payload.statut)
    except db.TransitionStatutInvalide as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} introuvable.")
    return document
