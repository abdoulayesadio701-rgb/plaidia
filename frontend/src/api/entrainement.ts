/**
 * entrainement.ts — Client typé pour /api/entrainement (backend/app/routers/entrainement.py).
 */

import { apiRequest, apiRequestBlob } from "./http";
import type { BilanEntrainement, SectionMesuree } from "./types";

export function enregistrerBilan(dossierId: number, sections: SectionMesuree[]): Promise<BilanEntrainement> {
  return apiRequest<BilanEntrainement>("/api/entrainement/", { method: "POST", body: { dossier_id: dossierId, sections } });
}

export function exporterBilan(dossierId: number, bilan: BilanEntrainement): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/entrainement/export", {
    method: "POST",
    body: {
      dossier_id: dossierId,
      sections: bilan.sections,
      total_alloue_secondes: bilan.total_alloue_secondes,
      total_reel_secondes: bilan.total_reel_secondes,
      total_ecart_secondes: bilan.total_ecart_secondes,
    },
  });
}
