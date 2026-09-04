/**
 * useActivityStore — compteur global de requêtes API en vol, utilisé par
 * StatusBar pour afficher "Prêt" / "Traitement en cours (Ns)".
 *
 * Séparé de useAppStore (dossier/espace/juridiction/chat) délibérément :
 * src/api/http.ts l'importe pour signaler chaque requête, et useAppStore
 * appelle des fonctions de src/api/*.ts pour rafraîchir ses données — les
 * garder dans le même fichier créerait un cycle d'imports (store -> api ->
 * store). Ce petit store n'importe jamais l'API, il ne fait qu'être lu par
 * elle : le cycle n'existe pas.
 */

import { create } from "zustand";

interface ActivityState {
  enCours: number;
  depuis: number | null;
  demarrer: () => void;
  terminer: () => void;
}

export const useActivityStore = create<ActivityState>((set) => ({
  enCours: 0,
  depuis: null,
  demarrer: () =>
    set((s) => ({ enCours: s.enCours + 1, depuis: s.depuis ?? Date.now() })),
  terminer: () =>
    set((s) => {
      const enCours = Math.max(0, s.enCours - 1);
      return { enCours, depuis: enCours === 0 ? null : s.depuis };
    }),
}));
