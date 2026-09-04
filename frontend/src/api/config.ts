/**
 * config.ts — GET /api/config (backend/app/main.py), consommé au montage
 * de l'app pour savoir s'il faut afficher le bandeau "Mode démo".
 */

import { apiRequest } from "./http";

export interface ConfigServeur {
  demo_mode: boolean;
  max_texte_caracteres: number;
  dossier_demo_nom: string | null;
}

export function obtenirConfiguration(): Promise<ConfigServeur> {
  return apiRequest<ConfigServeur>("/api/config");
}
