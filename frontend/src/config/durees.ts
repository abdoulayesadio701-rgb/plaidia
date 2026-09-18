/** durees.ts — formatage de durées en secondes, partagé par l'entraînement
 * chronométré et le tableau de bord du dossier. */

export function formaterDuree(secondes: number): string {
  const signe = secondes < 0 ? "-" : "";
  const abs = Math.abs(secondes);
  return `${signe}${Math.floor(abs / 60)} min ${String(abs % 60).padStart(2, "0")} s`;
}

export function formaterChrono(secondes: number): string {
  return `${String(Math.floor(secondes / 60)).padStart(2, "0")}:${String(secondes % 60).padStart(2, "0")}`;
}
