/**
 * useBrouillonPersistant — persistance locale (localStorage) pour les
 * pages indépendantes de tout dossier (Traduire, Analyse stylistique,
 * Extraction, Classement, Cohérence, PV d'audience...) : contrairement aux
 * pages Arsenal/Greffier liées à un dossier (voir useDernierDocumentGenere),
 * il n'y a pas de dossier_id auquel rattacher une entrée `documents_generes`
 * côté serveur -- ces outils sont volontairement indépendants de toute
 * affaire. La persistance se fait donc côté navigateur : le brouillon
 * survit à une navigation ou un F5, mais reste propre à cet appareil (pas
 * de synchronisation entre navigateurs/appareils, contrairement aux pages
 * liées à un dossier).
 */

import { useEffect, useState, type Dispatch, type SetStateAction } from "react";

function lire<T>(cle: string): T | null {
  try {
    const brut = localStorage.getItem(cle);
    return brut !== null ? (JSON.parse(brut) as T) : null;
  } catch {
    return null;
  }
}

function ecrire<T>(cle: string, valeur: T | null): void {
  try {
    if (valeur === null || valeur === undefined) localStorage.removeItem(cle);
    else localStorage.setItem(cle, JSON.stringify(valeur));
  } catch {
    // Stockage indisponible (navigation privée, quota dépassé) -- le
    // brouillon ne survivra pas au refresh, mais la page reste utilisable.
  }
}

/** Une valeur simple (texte saisi, liste de documents...) qui se comporte
 * comme useState (mises à jour fonctionnelles comprises) mais
 * restaure/persiste automatiquement dans localStorage. */
export function useValeurPersistante<T>(cle: string, valeurInitiale: T): [T, Dispatch<SetStateAction<T>>] {
  const [valeur, setValeur] = useState<T>(() => lire<T>(cle) ?? valeurInitiale);
  useEffect(() => {
    ecrire(cle, valeur);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cle, valeur]);
  return [valeur, setValeur];
}

/** Résultat d'une génération (useLazyAction/useLazyStream) : restauré une
 * fois au montage via `definirDonnees`, puis persisté à chaque changement. */
export function useResultatPersistant<T>(cle: string, donnees: T | null, definirDonnees: (v: T) => void): void {
  useEffect(() => {
    const restaure = lire<T>(cle);
    if (restaure !== null) definirDonnees(restaure);
    // Restauration au montage seulement -- ne pas relire à chaque frappe.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cle]);

  useEffect(() => {
    ecrire(cle, donnees);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cle, donnees]);
}

/** Efface un ou plusieurs brouillons (bouton « Supprimer », après
 * confirmation) -- à appeler en plus de la réinitialisation du state local
 * de la page (reinitialiser() de useLazyAction, setTexte("")...). */
export function effacerBrouillons(...cles: string[]): void {
  for (const cle of cles) ecrire(cle, null);
}
