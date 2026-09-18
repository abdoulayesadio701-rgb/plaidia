/**
 * seancesEntrainement.ts — résumé et comparaison des séances d'entraînement
 * déjà enregistrées pour un dossier (une entrée documents_generes par
 * séance). Fonctions pures.
 */

import type { BilanEntrainement, DocumentGenere } from "@/api";

export interface SeanceResume {
  id: number;
  date: string;
  alloueSecondes: number;
  reelSecondes: number;
  ecartSecondes: number;
  /** Rapprochement du temps prévu par rapport à la séance précédente :
   * > 0 = plus proche du plan (|écart| réduit), < 0 = plus éloigné, null =
   * pas de séance antérieure à comparer. */
  progresSecondes: number | null;
}

/** Séances triées de la plus récente à la plus ancienne. */
export function resumerSeances(documents: DocumentGenere[]): SeanceResume[] {
  const utilisables = documents
    .filter((d) => typeof d.contenu.total_ecart_secondes === "number")
    .sort((a, b) => b.date_modification.localeCompare(a.date_modification) || b.id - a.id);

  return utilisables.map((document, i) => {
    const bilan = document.contenu as unknown as BilanEntrainement;
    const precedente = utilisables[i + 1]?.contenu as unknown as BilanEntrainement | undefined;
    return {
      id: document.id,
      date: document.date_modification,
      alloueSecondes: bilan.total_alloue_secondes,
      reelSecondes: bilan.total_reel_secondes,
      ecartSecondes: bilan.total_ecart_secondes,
      progresSecondes: precedente
        ? Math.abs(precedente.total_ecart_secondes) - Math.abs(bilan.total_ecart_secondes)
        : null,
    };
  });
}
