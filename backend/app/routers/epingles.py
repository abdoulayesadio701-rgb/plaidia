"""
/api/epingles — Épinglage : un pointeur (type + reference_id) vers un
dossier ou une analyse déjà existant, jamais une copie de son contenu (voir
db.py::epingler). Toute la logique métier vient de db.py.

Portée volontairement limitée à "dossier" et "analyse" (voir
AUDIT_TASKBAR.md) : ce sont les deux seuls types d'éléments qui ont
aujourd'hui à la fois un identifiant stable en base ET un endroit réel où
les rouvrir -- un plan de plaidoirie, un simulateur d'objections ou une
conversation de chat n'ont pas encore cette persistance/cette UI de
navigation, les épingler créerait un raccourci vers rien.
"""

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
    if payload.type == "dossier":
        get_dossier_or_404(payload.reference_id)
        dossier_id = payload.reference_id
    else:  # "analyse"
        if payload.dossier_id is None:
            raise HTTPException(status_code=422, detail="dossier_id est requis pour épingler une analyse.")
        get_dossier_or_404(payload.dossier_id)
        ids_valides = {a["id"] for a in db.get_analyses_for_dossier(payload.dossier_id)}
        if payload.reference_id not in ids_valides:
            raise HTTPException(status_code=404, detail=f"Analyse {payload.reference_id} introuvable pour ce dossier.")
        dossier_id = payload.dossier_id

    existant = db.deja_epingle(payload.type, payload.reference_id)
    if existant:
        return dict(existant)

    pin_id = db.epingler(payload.type, payload.reference_id, dossier_id, payload.libelle)
    return dict(next(e for e in db.lister_epingles() if e["id"] == pin_id))


@router.delete("/{pin_id}", status_code=204)
def desepingler(pin_id: int):
    db.desepingler(pin_id)
