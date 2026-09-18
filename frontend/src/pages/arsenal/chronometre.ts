/**
 * chronometre.ts — arithmétique du chronomètre d'entraînement, avec pause.
 * Fonctions pures : l'instant courant est toujours passé en paramètre, ce
 * qui les rend testables sans horloge simulée.
 *
 * `debut` est reculé de la durée de chaque pause à la reprise : le temps
 * écoulé se calcule donc toujours `maintenant - debut`, sans cumul à tenir.
 */

export interface EtatChrono {
  debut: number;
  pauseDepuis: number | null;
}

export function demarrerChrono(maintenant: number): EtatChrono {
  return { debut: maintenant, pauseDepuis: null };
}

export function secondesEcoulees(etat: EtatChrono, maintenant: number): number {
  const reference = etat.pauseDepuis ?? maintenant;
  return Math.max(0, Math.round((reference - etat.debut) / 1000));
}

export function mettreEnPause(etat: EtatChrono, maintenant: number): EtatChrono {
  return etat.pauseDepuis === null ? { ...etat, pauseDepuis: maintenant } : etat;
}

export function reprendre(etat: EtatChrono, maintenant: number): EtatChrono {
  if (etat.pauseDepuis === null) return etat;
  return { debut: etat.debut + (maintenant - etat.pauseDepuis), pauseDepuis: null };
}
