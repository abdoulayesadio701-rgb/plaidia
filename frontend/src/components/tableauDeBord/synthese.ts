/**
 * synthese.ts — agrégation, côté navigateur, des documents déjà enregistrés
 * pour un dossier (GET /api/dossiers/{id}/documents-generes) en quelques
 * indicateurs pour la page d'accueil. Fonctions pures, sans appel réseau.
 *
 * Pour les fonctionnalités qui produisent un nouveau document à chaque
 * calcul (délais, entraînement), seul le plus récent fait foi -- comme sur
 * leurs pages respectives.
 */

import { joursRestants } from "@/config/echeances";
import type { BilanEntrainement, DelaiCalcule, DocumentGenere } from "@/api";

/** Features qui ont leur propre carte : exclues de la liste « récents ». */
const FEATURES_AVEC_CARTE = new Set(["delais", "bordereau", "entrainement"]);
const NOMBRE_RECENTS = 5;

/** Le strict nécessaire d'un délai pour évaluer son échéance. */
export interface EcheanceSimple {
  libelle: string;
  date_echeance: string;
}

export interface EcheanceProche<T extends EcheanceSimple = DelaiCalcule> {
  delai: T;
  jours: number;
}

/** Prochaine échéance non dépassée (une échéance à la date du jour compte
 * pour 0 jour) et nombre d'échéances déjà dépassées. */
export function evaluerEcheances<T extends EcheanceSimple>(
  delais: T[],
  maintenant: Date = new Date()
): { prochaine: EcheanceProche<T> | null; depassees: number } {
  let prochaine: EcheanceProche<T> | null = null;
  let depassees = 0;
  for (const delai of delais) {
    const jours = joursRestants(delai.date_echeance, maintenant);
    if (jours < 0) depassees += 1;
    else if (prochaine === null || jours < prochaine.jours) prochaine = { delai, jours };
  }
  return { prochaine, depassees };
}

export interface SyntheseDossier {
  prochaineEcheance: EcheanceProche | null;
  echeancesDepassees: number;
  nombrePieces: number | null;
  dernierEntrainement: BilanEntrainement | null;
  recents: DocumentGenere[];
}

function plusRecents(documents: DocumentGenere[]): DocumentGenere[] {
  return [...documents].sort(
    (a, b) => b.date_modification.localeCompare(a.date_modification) || b.id - a.id
  );
}

function dernierDeFeature(documents: DocumentGenere[], feature: string): DocumentGenere | null {
  return plusRecents(documents).find((d) => d.feature === feature) ?? null;
}

export function synthetiser(documents: DocumentGenere[], maintenant: Date = new Date()): SyntheseDossier {
  const docDelais = dernierDeFeature(documents, "delais");
  const delais = docDelais && Array.isArray(docDelais.contenu.delais) ? (docDelais.contenu.delais as DelaiCalcule[]) : [];
  const { prochaine: prochaineEcheance, depassees: echeancesDepassees } = evaluerEcheances(delais, maintenant);

  const docBordereau = dernierDeFeature(documents, "bordereau");
  const nombrePieces =
    docBordereau && Array.isArray(docBordereau.contenu.pieces) ? docBordereau.contenu.pieces.length : null;

  const docEntrainement = dernierDeFeature(documents, "entrainement");
  const dernierEntrainement =
    docEntrainement && Array.isArray(docEntrainement.contenu.sections)
      ? (docEntrainement.contenu as unknown as BilanEntrainement)
      : null;

  const recents = plusRecents(documents)
    .filter((d) => !FEATURES_AVEC_CARTE.has(d.feature))
    .slice(0, NOMBRE_RECENTS);

  return { prochaineEcheance, echeancesDepassees, nombrePieces, dernierEntrainement, recents };
}
