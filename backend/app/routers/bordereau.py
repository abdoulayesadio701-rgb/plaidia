"""
/api/bordereau — bordereau de pièces d'un dossier (liste numérotée des pièces
communiquées), pour les espaces Avocat et Greffier.

Stocké dans une seule entrée documents_generes (feature="bordereau") par
dossier, mise à jour sur place à chaque enregistrement -- ce qui le rend
retrouvable via « Documents générés » et la recherche transversale. Aucun
appel modèle : identique en mode démo.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import os

import db
import export as legacy_export
from app import bordereau
from app.deps import get_dossier_or_404
from app.schemas.bordereau import BordereauIn, BordereauOut
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/bordereau", tags=["bordereau"])

FEATURE = "bordereau"


def _document_du_dossier(dossier_id: int):
    documents = db.lister_documents_generes(dossier_id, FEATURE)
    return documents[0] if documents else None


def _sortie(document) -> BordereauOut:
    if document is None:
        return BordereauOut()
    return BordereauOut(pieces=document["contenu"].get("pieces", []), document_id=document["id"])


@router.get("/{dossier_id}", response_model=BordereauOut)
def lire_bordereau(dossier_id: int):
    get_dossier_or_404(dossier_id)
    return _sortie(_document_du_dossier(dossier_id))


@router.put("/{dossier_id}", response_model=BordereauOut)
def enregistrer_bordereau(dossier_id: int, payload: BordereauIn):
    dossier = get_dossier_or_404(dossier_id)
    contenu = {"pieces": [p.model_dump() for p in sorted(payload.pieces, key=lambda p: p.numero)]}
    existant = _document_du_dossier(dossier_id)
    if existant is None:
        document = db.creer_document_genere(dossier_id, FEATURE, f"Bordereau de pièces — {dossier['nom']}", {}, contenu)
    else:
        document = db.mettre_a_jour_document_genere(existant["id"], contenu)
    return _sortie(document)


@router.get("/{dossier_id}/sources", response_model=list[str])
def sources_importees(dossier_id: int):
    """Noms des documents déjà importés dans ce dossier, pour préremplir
    l'intitulé d'une pièce."""
    dossier = get_dossier_or_404(dossier_id)
    return bordereau.extraire_sources(dossier.get("faits") or "")


@router.get("/{dossier_id}/export")
def exporter_bordereau(dossier_id: int):
    dossier = get_dossier_or_404(dossier_id)
    document = _document_du_dossier(dossier_id)
    pieces = document["contenu"].get("pieces", []) if document else []
    pieces_formatees = [{**p, "date": bordereau.formater_date(p.get("date", ""))} for p in pieces]
    chemin = legacy_export.exporter_bordereau_word("Bordereau de pièces communiquées", dossier["nom"], pieces_formatees)
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
