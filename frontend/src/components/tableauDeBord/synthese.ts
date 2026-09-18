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

export interface EcheanceProche {
  delai: DelaiCalcule;
  jours: number;
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
  let prochaineEcheance: EcheanceProche | null = null;
  let echeancesDepassees = 0;
  const docDelais = dernierDeFeature(documents, "delais");
  const delais = docDelais && Array.isArray(docDelais.contenu.delais) ? (docDelais.contenu.delais as DelaiCalcule[]) : [];
  for (const delai of delais) {
    const jours = joursRestants(delai.date_echeance, maintenant);
    if (jours < 0) {
      echeancesDepassees += 1;
    } else if (prochaineEcheance === null || jours < prochaineEcheance.jours) {
      prochaineEcheance = { delai, jours };
    }
  }

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
