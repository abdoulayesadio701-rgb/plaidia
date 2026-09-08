/**
 * greffier.ts — Client typé pour /api/greffier (backend/app/routers/greffier.py).
 */

import { apiRequest, apiRequestBlob } from "./http";
import type {
  ChronologieResultat,
  ClassementResultat,
  CoherenceResultat,
  DocumentACoherence,
  ExtractionResultat,
  PvAudienceResultat,
  RapportInstructionResultat,
  RechercheDossierResultat,
  RequisitoireResultat,
  VerificationProceduraleResultat,
} from "./types";

export function chronologie(dossierId: number): Promise<ChronologieResultat> {
  return apiRequest<ChronologieResultat>("/api/greffier/chronologie", { method: "POST", body: { dossier_id: dossierId } });
}

export function exporterChronologie(dossierId: number, resultat: ChronologieResultat): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/greffier/chronologie/export", {
    method: "POST",
    body: { dossier_id: dossierId, evenements: resultat.evenements, periode_couverte: resultat.periode_couverte },
  });
}

export function extraction(texte: string): Promise<ExtractionResultat> {
  return apiRequest<ExtractionResultat>("/api/greffier/extraction", { method: "POST", body: { texte } });
}

export function classement(texte: string): Promise<ClassementResultat> {
  return apiRequest<ClassementResultat>("/api/greffier/classement", { method: "POST", body: { texte } });
}

export function controleCoherence(documents: DocumentACoherence[]): Promise<CoherenceResultat> {
  return apiRequest<CoherenceResultat>("/api/greffier/coherence", { method: "POST", body: { documents } });
}

export function rechercheTransversale(terme: string): Promise<RechercheDossierResultat[]> {
  return apiRequest<RechercheDossierResultat[]>("/api/greffier/recherche", { query: { terme } });
}

export function pvAudience(notes: string): Promise<PvAudienceResultat> {
  return apiRequest<PvAudienceResultat>("/api/greffier/pv-audience", { method: "POST", body: { notes } });
}

export function exporterPvAudience(texte: string, titre = "Procès-verbal d'audience"): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/greffier/pv-audience/export", { method: "POST", body: { texte, titre } });
}

export function verificationProcedurale(dossierId: number): Promise<VerificationProceduraleResultat> {
  return apiRequest<VerificationProceduraleResultat>("/api/greffier/verification-procedurale", {
    method: "POST",
    body: { dossier_id: dossierId },
  });
}

export function exporterVerificationProcedurale(
  dossierId: number,
  resultat: VerificationProceduraleResultat
): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob("/api/greffier/verification-procedurale/export", {
    method: "POST",
    body: {
      dossier_id: dossierId,
      echeances_identifiees: resultat.echeances_identifiees,
      actes_potentiellement_manquants: resultat.actes_potentiellement_manquants,
      points_attention: resultat.points_attention,
    },
  });
}

export function analyserRequisitoire(texte: string): Promise<RequisitoireResultat> {
  return apiRequest<RequisitoireResultat>("/api/greffier/requisitoire", { method: "POST", body: { texte } });
}

export function analyserRapportInstruction(texte: string): Promise<RapportInstructionResultat> {
  return apiRequest<RapportInstructionResultat>("/api/greffier/rapport-instruction", { method: "POST", body: { texte } });
}
