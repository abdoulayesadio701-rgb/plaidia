/**
 * notes.ts — Client typé pour /api/notes (backend/app/routers/notes.py).
 */

import { apiRequest, apiRequestBlob } from "./http";
import type { Note, NoteClientResultat } from "./types";

export function creerNote(dossierId: number, noteBrute: string): Promise<Note> {
  return apiRequest<Note>("/api/notes/", { method: "POST", body: { dossier_id: dossierId, note_brute: noteBrute } });
}

export function listerNotes(dossierId: number): Promise<Note[]> {
  return apiRequest<Note[]>(`/api/notes/dossier/${dossierId}`);
}

export function supprimerNote(noteId: number): Promise<void> {
  return apiRequest<void>(`/api/notes/${noteId}`, { method: "DELETE" });
}

export function exporterNotes(dossierId: number): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob(`/api/notes/dossier/${dossierId}/export`);
}

export function redigerNoteClient(dossierId: number): Promise<NoteClientResultat> {
  return apiRequest<NoteClientResultat>("/api/notes/note-client", { method: "POST", body: { dossier_id: dossierId } });
}

export function exporterNoteClient(dossierId: number, texte: string): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/notes/note-client/export", { method: "POST", body: { dossier_id: dossierId, texte } });
}
