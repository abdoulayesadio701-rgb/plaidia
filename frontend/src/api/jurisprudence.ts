/**
 * jurisprudence.ts — Client typé pour /api/jurisprudence
 * (backend/app/routers/jurisprudence.py).
 */

import { apiRequest, apiUpload } from "./http";
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

/** Import d'un texte de corpus à partir d'un fichier (PDF, DOCX, TXT...)
 * plutôt que d'un texte collé -- voir AUDIT_IMPORT_EXPORT.md. Les métadonnées
 * sont les mêmes que importerTexteCorpus, `contenu` en moins (extrait
 * côté serveur). */
export function importerFichierCorpus(fichier: File, meta: Omit<CorpusImportInput, "contenu">): Promise<CorpusTexte> {
  const formData = new FormData();
  formData.append("fichier", fichier);
  formData.append("source", meta.source);
  formData.append("pays", meta.pays ?? "");
  formData.append("type_texte", meta.type_texte ?? "");
  formData.append("domaine", meta.domaine ?? "");
  formData.append("reference", meta.reference ?? "");
  formData.append("date_texte", meta.date_texte ?? "");
  return apiUpload<CorpusTexte>("/api/jurisprudence/corpus/importer-fichier", formData);
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

/** Valide en un seul appel tous les textes en attente d'une même source
 * (voir db.py::valider_texte_corpus_par_source) — pour les imports en
 * masse où valider un par un serait irréaliste. `domaine` (optionnel)
 * restreint la validation à ce sous-ensemble précis de la source (ex. un
 * seul acte uniforme au sein d'un import OHADA de qualité inégale). */
export function validerCorpusParSource(source: string, domaine?: string): Promise<{ source: string; domaine: string; nombre_valide: number }> {
  return apiRequest<{ source: string; domaine: string; nombre_valide: number }>("/api/jurisprudence/corpus/valider-source", {
    method: "POST",
    body: { source, domaine: domaine ?? "" },
  });
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
