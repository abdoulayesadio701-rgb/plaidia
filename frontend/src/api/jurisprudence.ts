/**
 * jurisprudence.ts — Client typé pour /api/jurisprudence
 * (backend/app/routers/jurisprudence.py).
 */

import { apiRequest } from "./http";
import type { CollecterResultat, ConsulterResultat, CorpusImportInput, CorpusTexte, Jurisprudence } from "./types";

export function consulterJurisprudence(question: string, but = "", source = "Légifrance (France)"): Promise<ConsulterResultat> {
  return apiRequest<ConsulterResultat>("/api/jurisprudence/consulter", { method: "POST", body: { question, but, source } });
}

export function collecterJurisprudence(query: string, domaine = ""): Promise<CollecterResultat> {
  return apiRequest<CollecterResultat>("/api/jurisprudence/collecter", { method: "POST", body: { query, domaine } });
}

export function jurisprudenceEnAttente(domaine?: string): Promise<Jurisprudence[]> {
  return apiRequest<Jurisprudence[]>("/api/jurisprudence/en-attente", { query: { domaine } });
}

export function jurisprudenceValidee(domaine?: string): Promise<Jurisprudence[]> {
  return apiRequest<Jurisprudence[]>("/api/jurisprudence/validee", { query: { domaine } });
}

export function validerJurisprudence(id: number): Promise<void> {
  return apiRequest<void>(`/api/jurisprudence/${id}/valider`, { method: "POST" });
}

export function rejeterJurisprudence(id: number): Promise<void> {
  return apiRequest<void>(`/api/jurisprudence/${id}`, { method: "DELETE" });
}

export function importerTexteCorpus(input: CorpusImportInput): Promise<CorpusTexte> {
  return apiRequest<CorpusTexte>("/api/jurisprudence/corpus", { method: "POST", body: input });
}

export function corpusEnAttente(): Promise<CorpusTexte[]> {
  return apiRequest<CorpusTexte[]>("/api/jurisprudence/corpus/en-attente");
}

export function corpusValide(params: { source?: string; pays?: string; domaine?: string } = {}): Promise<CorpusTexte[]> {
  return apiRequest<CorpusTexte[]>("/api/jurisprudence/corpus/valide", { query: params });
}

export function sourcesCorpus(): Promise<string[]> {
  return apiRequest<string[]>("/api/jurisprudence/corpus/sources");
}

export function validerCorpus(id: number): Promise<void> {
  return apiRequest<void>(`/api/jurisprudence/corpus/${id}/valider`, { method: "POST" });
}

export function rejeterCorpus(id: number): Promise<void> {
  return apiRequest<void>(`/api/jurisprudence/corpus/${id}`, { method: "DELETE" });
}

export function obtenirJuridictionActive(): Promise<{ juridiction: string }> {
  return apiRequest<{ juridiction: string }>("/api/jurisprudence/juridiction-active");
}

export function definirJuridictionActive(juridiction: string): Promise<{ juridiction: string }> {
  return apiRequest<{ juridiction: string }>("/api/jurisprudence/juridiction-active", { method: "PUT", body: { juridiction } });
}
