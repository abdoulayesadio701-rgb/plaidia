/**
 * config.ts — GET /api/config (backend/app/main.py), consommé au montage
 * de l'app pour savoir s'il faut afficher le bandeau "Mode démo".
 */

import { apiRequest } from "./http";

export interface ConfigServeur {
  demo_mode: boolean;
  max_texte_caracteres: number;
  dossier_demo_nom: string | null;
  /** Vrai si le serveur exige un mot de passe d'accès (voir backend/app/acces.py). */
  acces_protege?: boolean;
  /** Commit déployé côté serveur (7 caractères), absent hors Render. */
  commit?: string | null;
}

export function obtenirConfiguration(): Promise<ConfigServeur> {
  return apiRequest<ConfigServeur>("/api/config");
}

/** Lève une ApiError 401 si le mot de passe stocké est absent ou faux. */
export function verifierAcces(): Promise<void> {
  return apiRequest<void>("/api/acces/verifier", { method: "POST" });
}
