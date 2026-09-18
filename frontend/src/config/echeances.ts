/**
 * echeances.ts — calculs d'affichage partagés par le suivi des délais
 * (DelaisPage) et le tableau de bord du dossier. Les dates d'échéance
 * viennent du backend au format AAAA-MM-JJ, sans fuseau : on les lit en
 * date locale pour ne jamais décaler d'un jour.
 */

const MS_PAR_JOUR = 86_400_000;

/** Une échéance à ce nombre de jours ou moins est signalée sur la liste des dossiers. */
export const SEUIL_ALERTE_JOURS = 7;

export function versDateLocale(iso: string): Date {
  const [annee, mois, jour] = iso.split("-").map(Number);
  return new Date(annee, mois - 1, jour);
}

export function joursRestants(echeanceIso: string, maintenant: Date = new Date()): number {
  const minuit = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate());
  return Math.round((versDateLocale(echeanceIso).getTime() - minuit.getTime()) / MS_PAR_JOUR);
}

export function classeUrgence(jours: number): string {
  if (jours <= 7) return "badge-risk-high";
  if (jours <= 30) return "badge-risk-medium";
  return "badge-risk-low";
}
