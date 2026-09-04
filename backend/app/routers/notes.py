"""
/api/notes — Prise de note structurée par l'IA, consultation des notes
d'un dossier, rédaction et export d'une note client en langage simple.

Toute la logique métier vient telle quelle de analyse.py, db.py et export.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import os

import analyse as legacy_analyse
import db
import export as legacy_export
from app import demo
from app.deps import construire_contexte_dossier, get_dossier_or_404
from app.schemas.notes import ExportNoteClientIn, NoteClientIn, NoteClientOut, NoteCreate, NoteOut
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.post("/", response_model=NoteOut, status_code=201)
def creer_note(payload: NoteCreate):
    get_dossier_or_404(payload.dossier_id)
    demo.exiger_cle_api()
    resultat = legacy_analyse.traiter_notes(payload.note_brute)
    note_id = db.ajouter_note(
        payload.dossier_id,
        payload.note_brute,
        note_structuree=resultat.get("note_structuree", ""),
        actions=resultat.get("actions_a_faire", []),
        points=resultat.get("points_a_retenir", []),
    )
    notes = db.get_notes_dossier(payload.dossier_id)
    return next(n for n in notes if n["id"] == note_id)


@router.get("/dossier/{dossier_id}", response_model=list[NoteOut])
def lister_notes(dossier_id: int):
    get_dossier_or_404(dossier_id)
    return db.get_notes_dossier(dossier_id)


@router.delete("/{note_id}", status_code=204)
def supprimer_note(note_id: int):
    db.delete_note(note_id)


@router.post("/note-client", response_model=NoteClientOut)
def rediger_note_client(payload: NoteClientIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    demo.exiger_cle_api()
    contexte = construire_contexte_dossier(dossier)
    texte = legacy_analyse.rediger_note_client(contexte)
    return NoteClientOut(texte=texte)


@router.post("/note-client/export")
def exporter_note_client(payload: ExportNoteClientIn):
    dossier = get_dossier_or_404(payload.dossier_id)
    chemin = legacy_export.exporter_note_client_word(dossier, payload.texte)
    return FileResponse(
        chemin,
        filename=os.path.basename(chemin),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
