/**
 * epingles.ts — Client typé pour /api/epingles (backend/app/routers/epingles.py).
 */

import { apiRequest } from "./http";
import type { ElementEpingle, TypeEpingle } from "./types";

export function listerEpingles(): Promise<ElementEpingle[]> {
  return apiRequest<ElementEpingle[]>("/api/epingles/");
}

export function epingler(type: TypeEpingle, referenceId: number, libelle: string, dossierId?: number | null): Promise<ElementEpingle> {
  return apiRequest<ElementEpingle>("/api/epingles/", {
    method: "POST",
    body: { type, reference_id: referenceId, dossier_id: dossierId ?? null, libelle },
  });
}

export function desepingler(pinId: number): Promise<void> {
  return apiRequest<void>(`/api/epingles/${pinId}`, { method: "DELETE" });
}
