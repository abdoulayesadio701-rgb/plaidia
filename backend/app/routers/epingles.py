"""API d'épingles : des pointeurs vers des éléments persistés, jamais des copies."""

from app.bootstrap import ROOT_DIR  # noqa: F401

import db
from app.deps import get_dossier_or_404
from app.schemas.epingles import EpingleOut, EpinglerIn
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/epingles", tags=["epingles"])


@router.get("/", response_model=list[EpingleOut])
def lister():
    return [dict(e) for e in db.lister_epingles()]


@router.post("/", response_model=EpingleOut, status_code=201)
def epingler(payload: EpinglerIn):
    if payload.type != "dossier" and payload.dossier_id is None:
        raise HTTPException(status_code=422, detail="dossier_id est requis pour épingler cet élément.")
    try:
        dossier_id = db.verifier_cible_epingle(payload.type, payload.reference_id, payload.dossier_id)
    except db.CibleEpingleIntrouvable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    existant = db.deja_epingle(payload.type, payload.reference_id)
    if existant:
        return dict(existant)

    pin_id = db.epingler(payload.type, payload.reference_id, dossier_id, payload.libelle)
    return dict(next(e for e in db.lister_epingles() if e["id"] == pin_id))


@router.delete("/{pin_id}", status_code=204)
def desepingler(pin_id: int):
    db.desepingler(pin_id)
