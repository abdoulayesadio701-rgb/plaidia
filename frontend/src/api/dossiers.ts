/**
 * dossiers.ts — Client typé pour /api/dossiers (backend/app/routers/dossiers.py).
 */

import { ApiError, apiRequest, apiRequestBlob, apiUpload, BASE_URL } from "./http";
import { useActivityStore } from "@/store/useActivityStore";
import type { AnalyseHistorique, DocumentImporte, Dossier, DossierCreateInput, RechercheDossierResultat } from "./types";

export function creerDossier(input: DossierCreateInput): Promise<Dossier> {
  return apiRequest<Dossier>("/api/dossiers/", { method: "POST", body: input });
}

export function listerDossiers(): Promise<Dossier[]> {
  return apiRequest<Dossier[]>("/api/dossiers/");
}

export function obtenirDossier(dossierId: number): Promise<Dossier> {
  return apiRequest<Dossier>(`/api/dossiers/${dossierId}`);
}

export function rechercherDossiers(terme: string): Promise<RechercheDossierResultat[]> {
  return apiRequest<RechercheDossierResultat[]>("/api/dossiers/recherche", { query: { terme } });
}

export function modifierDomaine(dossierId: number, domaine: string): Promise<Dossier> {
  return apiRequest<Dossier>(`/api/dossiers/${dossierId}/domaine`, { method: "PATCH", body: { domaine } });
}

export function supprimerDossier(dossierId: number): Promise<void> {
  return apiRequest<void>(`/api/dossiers/${dossierId}`, { method: "DELETE" });
}

export function historiqueAnalyses(dossierId: number): Promise<AnalyseHistorique[]> {
  return apiRequest<AnalyseHistorique[]>(`/api/dossiers/${dossierId}/analyses`);
}

export function ajouterAuxFaits(dossierId: number, texte: string, source = "texte collé"): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>(`/api/dossiers/${dossierId}/faits`, { method: "POST", body: { texte, source } });
}

export function importerDocument(dossierId: number, fichier: File): Promise<DocumentImporte> {
  const formData = new FormData();
  formData.append("fichier", fichier);
  return apiUpload<DocumentImporte>(`/api/dossiers/${dossierId}/documents`, formData);
}

/** Même extraction que importerDocument, mais sans rattacher le texte à un
 * dossier -- pour les pages volontairement indépendantes de tout dossier
 * (PV d'audience, contrôle de cohérence). N'écrit rien en base. */
export function extraireFichier(fichier: File): Promise<DocumentImporte> {
  const formData = new FormData();
  formData.append("fichier", fichier);
  return apiUpload<DocumentImporte>("/api/dossiers/extraire", formData);
}

export async function exporterFaitsBruts(dossierId: number): Promise<{ blob: Blob; filename?: string }> {
  return apiRequestBlob(`/api/dossiers/${dossierId}/export/faits-bruts`);
}

/**
 * Import d'un document avec suivi de progression réel (XMLHttpRequest --
 * `fetch`, utilisé par apiUpload, n'expose pas d'événement de progression
 * d'envoi). Réservé à PreparerDossierPage (glisser-déposer avec barre de
 * progression) ; le reste de l'app continue d'utiliser importerDocument().
 */
export function importerDocumentAvecProgression(
  dossierId: number,
  fichier: File,
  onProgression: (pourcentage: number) => void,
  signal?: AbortSignal
): Promise<DocumentImporte> {
  useActivityStore.getState().demarrer();
  let termine = false;
  const finirActivite = () => {
    if (!termine) {
      termine = true;
      useActivityStore.getState().terminer();
    }
  };

  return new Promise<DocumentImporte>((resolve, reject) => {
    const formData = new FormData();
    formData.append("fichier", fichier);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE_URL}/api/dossiers/${dossierId}/documents`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgression(Math.round((e.loaded / e.total) * 100));
    };

    xhr.onload = () => {
      finirActivite();
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as DocumentImporte);
        } catch {
          reject(new ApiError(xhr.status, null, "Réponse du serveur illisible."));
        }
        return;
      }
      let detail: unknown = null;
      let message = `Erreur ${xhr.status}`;
      try {
        const data = JSON.parse(xhr.responseText) as { detail?: unknown };
        detail = data?.detail ?? data;
        if (typeof detail === "string") message = detail;
      } catch {
        // Corps non-JSON (ex. 502 d'un proxy) -- on garde le message générique.
      }
      reject(new ApiError(xhr.status, detail, message));
    };

    xhr.onerror = () => {
      finirActivite();
      reject(new ApiError(0, null, "Impossible de joindre le serveur. Vérifiez que le backend est lancé (voir backend/README.md)."));
    };

    xhr.onabort = () => {
      finirActivite();
      reject(new DOMException("Import annulé.", "AbortError"));
    };

    if (signal) {
      if (signal.aborted) {
        xhr.abort();
        return;
      }
      signal.addEventListener("abort", () => xhr.abort());
    }

    xhr.send(formData);
  });
}
