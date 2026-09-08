/**
 * analyse.ts — Client typé pour /api/analyse (backend/app/routers/analyse.py).
 */

import { apiRequest, apiRequestBlob } from "./http";
import type { ConclusionsResultat, PlanResultat, RapportCompletResultat, ResumeResultat, SimulateurResultat, StyleResultat, TraductionResultat } from "./types";

export function analyserConclusions(texte: string, dossierId?: number): Promise<ConclusionsResultat> {
  return apiRequest<ConclusionsResultat>("/api/analyse/conclusions", {
    method: "POST",
    body: { texte, dossier_id: dossierId ?? null },
  });
}

export function resumerDossier(dossierId: number): Promise<ResumeResultat> {
  return apiRequest<ResumeResultat>("/api/analyse/resume", { method: "POST", body: { dossier_id: dossierId } });
}

export function genererPlan(dossierId: number, tempsMinutes: number): Promise<PlanResultat> {
  return apiRequest<PlanResultat>("/api/analyse/plan", {
    method: "POST",
    body: { dossier_id: dossierId, temps_minutes: tempsMinutes },
  });
}

export function simulerObjections(dossierId: number): Promise<SimulateurResultat> {
  return apiRequest<SimulateurResultat>("/api/analyse/simulateur", { method: "POST", body: { dossier_id: dossierId } });
}

export function exporterSimulateur(dossierId: number, resultat: SimulateurResultat): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/analyse/simulateur/export", {
    method: "POST",
    body: { dossier_id: dossierId, objections: resultat.objections, point_le_plus_faible: resultat.point_le_plus_faible },
  });
}

export function rapportComplet(dossierId: number, tempsMinutes?: number): Promise<RapportCompletResultat> {
  return apiRequest<RapportCompletResultat>("/api/analyse/rapport-complet", {
    method: "POST",
    body: { dossier_id: dossierId, temps_minutes: tempsMinutes ?? null },
  });
}

export function analyserStyle(texte: string): Promise<StyleResultat> {
  return apiRequest<StyleResultat>("/api/analyse/style", { method: "POST", body: { texte } });
}

export function traduireTexte(texte: string): Promise<TraductionResultat> {
  return apiRequest<TraductionResultat>("/api/analyse/traduire", { method: "POST", body: { texte } });
}

export function exporterConclusions(
  dossierId: number,
  argumentsData: ConclusionsResultat["arguments"],
  pointsAttention: string[],
  format: "word" | "pdf" = "word"
): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/analyse/conclusions/export", {
    method: "POST",
    query: { format },
    body: { dossier_id: dossierId, arguments: argumentsData, points_attention: pointsAttention },
  });
}

export function exporterRapportComplet(
  dossierId: number,
  analyse: ConclusionsResultat | null,
  plan: PlanResultat | null,
  simulateur: SimulateurResultat | null
): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/analyse/rapport-complet/export", {
    method: "POST",
    body: { dossier_id: dossierId, analyse, plan, simulateur },
  });
}
