/**
 * analyse.ts — Client typé pour /api/analyse (backend/app/routers/analyse.py).
 */

import { apiRequest, apiRequestBlob, BASE_URL } from "./http";
import { obtenirClePersonnelle } from "./cleApiPersonnelle";
import { entetesSse, lireFluxSse } from "./sse";
import type { ConclusionsResultat, DocumentGenere, PlanResultat, RapportCompletResultat, ResumeResultat, SimulateurResultat, StatutDocument, StyleResultat, TraductionResultat, Verification } from "./types";

export function analyserConclusions(texte: string, dossierId?: number): Promise<ConclusionsResultat> {
  return apiRequest<ConclusionsResultat>("/api/analyse/conclusions", {
    method: "POST",
    body: { texte, dossier_id: dossierId ?? null },
  });
}

/** Étape affichée par l'indicateur de progression pendant une génération en
 * streaming (chantier "temps de traitement des générations", §3). */
export interface EtapePipeline {
  etape: string;
  libelle: string;
}

interface CallbacksFluxPipeline<Principal> {
  onEtape?: (etape: EtapePipeline) => void;
  onPrincipal?: (patch: Partial<Principal>) => void;
  onVerification?: (verification: Verification) => void;
  onDocument?: (patch: Partial<Principal>) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

function entetesAvecClePersonnelle(): Record<string, string> {
  const headers = entetesSse();
  const clePersonnelle = obtenirClePersonnelle();
  if (clePersonnelle) headers["X-Anthropic-Api-Key"] = clePersonnelle;
  return headers;
}

/**
 * Variante en streaming de analyserConclusions() (§2a) : `onPrincipal` est
 * appelé dès que l'agent principal a produit ses arguments -- avant que le
 * vérificateur et le critique n'aient tourné -- puis `onVerification`
 * arrive séparément, une fois prête. Voir POST /api/analyse/conclusions/stream
 * (backend/app/routers/analyse.py).
 */
export function streamAnalyserConclusions(
  texte: string,
  dossierId: number | undefined,
  callbacks: CallbacksFluxPipeline<ConclusionsResultat>,
  signal?: AbortSignal
): Promise<void> {
  return lireFluxSse(
    `${BASE_URL}/api/analyse/conclusions/stream`,
    { method: "POST", headers: entetesAvecClePersonnelle(), body: JSON.stringify({ texte, dossier_id: dossierId ?? null }), signal },
    {
      etape: (data) => callbacks.onEtape?.(data as EtapePipeline),
      principal: (data) => callbacks.onPrincipal?.(data as Partial<ConclusionsResultat>),
      verification: (data) => callbacks.onVerification?.((data as { verification: Verification }).verification),
      document: (data) => callbacks.onDocument?.(data as Partial<ConclusionsResultat>),
      done: () => callbacks.onDone?.(),
      error: (data) => callbacks.onError?.((data as { detail: string }).detail),
    },
    callbacks.onError
  );
}

/** Variante en streaming de genererPlan() (§2a) -- voir POST
 * /api/analyse/plan/stream (backend/app/routers/analyse.py). */
export function streamGenererPlan(
  dossierId: number,
  tempsMinutes: number,
  callbacks: CallbacksFluxPipeline<PlanResultat>,
  signal?: AbortSignal
): Promise<void> {
  return lireFluxSse(
    `${BASE_URL}/api/analyse/plan/stream`,
    { method: "POST", headers: entetesAvecClePersonnelle(), body: JSON.stringify({ dossier_id: dossierId, temps_minutes: tempsMinutes }), signal },
    {
      etape: (data) => callbacks.onEtape?.(data as EtapePipeline),
      principal: (data) => callbacks.onPrincipal?.(data as Partial<PlanResultat>),
      verification: (data) => callbacks.onVerification?.((data as { verification: Verification }).verification),
      document: (data) => callbacks.onDocument?.(data as Partial<PlanResultat>),
      done: () => callbacks.onDone?.(),
      error: (data) => callbacks.onError?.((data as { detail: string }).detail),
    },
    callbacks.onError
  );
}

export function changerStatutConclusion(analyseId: number, statut: StatutDocument): Promise<{ analyse_id: number; statut: StatutDocument }> {
  return apiRequest<{ analyse_id: number; statut: StatutDocument }>(`/api/analyse/conclusions/${analyseId}/statut`, {
    method: "PATCH",
    body: { statut },
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

export function obtenirDocumentGenere(id: number): Promise<DocumentGenere> {
  return apiRequest<DocumentGenere>(`/api/documents-generes/${id}`);
}

export function changerStatutDocument(id: number, statut: StatutDocument): Promise<DocumentGenere> {
  return apiRequest<DocumentGenere>(`/api/documents-generes/${id}/statut`, { method: "PATCH", body: { statut } });
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
