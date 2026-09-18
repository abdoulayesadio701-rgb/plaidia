/**
 * bordereau.ts — Client typé pour /api/bordereau (backend/app/routers/bordereau.py).
 */

import { apiRequest, apiRequestBlob } from "./http";
import type { Bordereau, PieceBordereau } from "./types";

export function lireBordereau(dossierId: number): Promise<Bordereau> {
  return apiRequest<Bordereau>(`/api/bordereau/${dossierId}`);
}

export function enregistrerBordereau(dossierId: number, pieces: PieceBordereau[]): Promise<Bordereau> {
  return apiRequest<Bordereau>(`/api/bordereau/${dossierId}`, { method: "PUT", body: { pieces } });
}

export function sourcesImportees(dossierId: number): Promise<string[]> {
  return apiRequest<string[]>(`/api/bordereau/${dossierId}/sources`);
}

export function exporterBordereau(dossierId: number): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob(`/api/bordereau/${dossierId}/export`);
}
