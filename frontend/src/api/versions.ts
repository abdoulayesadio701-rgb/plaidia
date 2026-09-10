/**
 * versions.ts — Client typé pour /api/versions (backend/app/routers/versions.py).
 */

import { apiRequest } from "./http";
import type { VersionDocument } from "./types";

export function listerVersions(feature: string, dossierId?: number | null): Promise<VersionDocument[]> {
  return apiRequest<VersionDocument[]>("/api/versions/", { query: { feature, dossier_id: dossierId ?? undefined } });
}

export function restaurerVersion(versionId: number): Promise<VersionDocument> {
  return apiRequest<VersionDocument>(`/api/versions/${versionId}/restaurer`, { method: "POST" });
}
