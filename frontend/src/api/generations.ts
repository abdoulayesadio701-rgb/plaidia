/**
 * generations.ts — Client typé pour /api/generations
 * (backend/app/routers/generations.py) -- générations en arrière-plan,
 * portage web de gui.py::PlaidIAApp._lancer_generation.
 */

import { apiRequest } from "./http";
import type { Generation, GenerationLancee } from "./types";

export function lancerConclusions(texte: string, dossierId?: number | null): Promise<GenerationLancee> {
  return apiRequest<GenerationLancee>("/api/generations/conclusions", {
    method: "POST",
    body: { texte, dossier_id: dossierId ?? null },
  });
}

export function lancerPlan(dossierId: number, tempsMinutes: number): Promise<GenerationLancee> {
  return apiRequest<GenerationLancee>("/api/generations/plan", {
    method: "POST",
    body: { dossier_id: dossierId, temps_minutes: tempsMinutes },
  });
}

export function listerGenerations(dossierId?: number): Promise<Generation[]> {
  return apiRequest<Generation[]>("/api/generations/", { query: { dossier_id: dossierId } });
}

export function obtenirGeneration(id: number): Promise<Generation> {
  return apiRequest<Generation>(`/api/generations/${id}`);
}

/** Suppression DÉFINITIVE, sur action explicite uniquement -- jamais
 * d'expiration ni de nettoyage automatique (voir db.supprimer_generation). */
export function supprimerGeneration(id: number): Promise<void> {
  return apiRequest<void>(`/api/generations/${id}`, { method: "DELETE" });
}
