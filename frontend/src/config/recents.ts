/**
 * recents.ts — Historique des dernières pages consultées, entièrement côté
 * client (localStorage), pas de nouvelle table backend : « récents » est de
 * l'historique de navigation, pas une donnée métier à synchroniser entre
 * appareils (voir AUDIT_TASKBAR.md §E). Suit la même convention manuelle
 * que api/cleApiPersonnelle.ts plutôt qu'un middleware zustand/persist,
 * pour rester cohérent avec useAppStore ("sans middleware superflu").
 */

export interface ElementRecent {
  /** chemin + dossier, pour dédupliquer une même page revisitée avec le même dossier actif. */
  id: string;
  /** chemin relatif à /app, ex. "/arsenal/analyser". */
  path: string;
  label: string;
  dossierId: number | null;
  dossierNom: string | null;
  date: string;
}

const CLE_STOCKAGE = "plaidia_recents_v1";
const MAX_RECENTS = 12;
const EVENEMENT_CHANGEMENT = "plaidia:recents-changed";

function lire(): ElementRecent[] {
  try {
    const brut = localStorage.getItem(CLE_STOCKAGE);
    return brut ? (JSON.parse(brut) as ElementRecent[]) : [];
  } catch {
    return [];
  }
}

function ecrire(liste: ElementRecent[]) {
  try {
    localStorage.setItem(CLE_STOCKAGE, JSON.stringify(liste));
  } catch {
    // Stockage indisponible (navigation privée, quota...) -- "récents"
    // reste simplement vide pour cette session, jamais bloquant.
  }
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(EVENEMENT_CHANGEMENT));
  }
}

export function ajouterRecent(entree: Omit<ElementRecent, "date">) {
  const liste = lire().filter((e) => e.id !== entree.id);
  liste.unshift({ ...entree, date: new Date().toISOString() });
  ecrire(liste.slice(0, MAX_RECENTS));
}

export function listerRecents(): ElementRecent[] {
  return lire();
}

export function viderRecents() {
  ecrire([]);
}

export function ecouterChangementsRecents(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(EVENEMENT_CHANGEMENT, callback);
  return () => window.removeEventListener(EVENEMENT_CHANGEMENT, callback);
}
