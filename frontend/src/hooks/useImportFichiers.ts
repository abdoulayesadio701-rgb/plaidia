/**
 * useImportFichiers — gestion générique d'un import multi-fichiers avec
 * suivi détaillé : validation d'extension, file d'attente séquentielle (le
 * backend traite un fichier à la fois, voir extract.py), statut par fichier
 * (en_attente/en_cours/termine/erreur), progression, annulation, retrait.
 *
 * Extrait de PreparerDossierPage (le premier endroit où ce comportement
 * complet a été construit) pour être réutilisé partout où un import
 * multi-fichiers avec suivi apporte une vraie valeur (voir
 * AUDIT_IMPORT_EXPORT.md) — pas pour les pages qui se contentent d'un
 * bouton d'import simple, qui gèrent leur propre état de chargement.
 */

import { useCallback, useRef, useState } from "react";
import type { DocumentImporte } from "@/api";

export type StatutFichierImport = "en_attente" | "en_cours" | "termine" | "erreur";

export interface FichierSuivi {
  id: string;
  nom: string;
  taille: number;
  statut: StatutFichierImport;
  progression: number;
  erreur?: string;
  caracteresExtraits?: number;
  controller: AbortController;
}

/** Signature commune à dossiersApi.importerDocumentAvecProgression et à
 * tout futur import avec progression -- onProgression/signal sont ignorés
 * sans erreur par une fonction d'extraction plus simple qui ne les prend
 * pas en paramètre. */
export type FonctionExtractionAvecSuivi = (
  fichier: File,
  onProgression: (pourcentage: number) => void,
  signal: AbortSignal
) => Promise<DocumentImporte>;

interface UseImportFichiersOptions {
  extensionsAutorisees: string[];
  extraire: FonctionExtractionAvecSuivi;
  /** Appelé après extraction réussie d'un fichier -- pour intégrer le texte
   * extrait à l'endroit voulu par la page appelante (faits du dossier,
   * corpus, textarea...). */
  onExtrait?: (resultat: DocumentImporte, fichier: File) => void;
}

function extensionAutorisee(nom: string, extensions: string[]): boolean {
  const idx = nom.lastIndexOf(".");
  if (idx === -1) return false;
  return extensions.includes(nom.slice(idx).toLowerCase());
}

export function useImportFichiers({ extensionsAutorisees, extraire, onExtrait }: UseImportFichiersOptions) {
  const [fichiers, setFichiers] = useState<FichierSuivi[]>([]);
  const fileQueue = useRef<Promise<void>>(Promise.resolve());

  const majFichier = useCallback((id: string, patch: Partial<FichierSuivi>) => {
    setFichiers((liste) => liste.map((f) => (f.id === id ? { ...f, ...patch } : f)));
  }, []);

  const traiterFichier = useCallback(
    async (suivi: FichierSuivi, fichier: File) => {
      majFichier(suivi.id, { statut: "en_cours" });
      try {
        const resultat = await extraire(fichier, (pourcentage) => majFichier(suivi.id, { progression: pourcentage }), suivi.controller.signal);
        majFichier(suivi.id, { statut: "termine", progression: 100, caracteresExtraits: resultat.caracteres_extraits });
        onExtrait?.(resultat, fichier);
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") {
          majFichier(suivi.id, { statut: "erreur", erreur: "Import annulé." });
          return;
        }
        majFichier(suivi.id, { statut: "erreur", erreur: e instanceof Error ? e.message : "Échec de l'import." });
      }
    },
    [extraire, onExtrait, majFichier]
  );

  const ajouterFichiers = useCallback(
    (liste: FileList | File[]) => {
      const fichiersValides: { fichier: File; suivi: FichierSuivi }[] = [];
      for (const fichier of Array.from(liste)) {
        const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        if (!extensionAutorisee(fichier.name, extensionsAutorisees)) {
          setFichiers((l) => [
            ...l,
            {
              id,
              nom: fichier.name,
              taille: fichier.size,
              statut: "erreur",
              progression: 0,
              erreur: `Format non supporté (formats acceptés : ${extensionsAutorisees.join(", ")}).`,
              controller: new AbortController(),
            },
          ]);
          continue;
        }
        const suivi: FichierSuivi = {
          id,
          nom: fichier.name,
          taille: fichier.size,
          statut: "en_attente",
          progression: 0,
          controller: new AbortController(),
        };
        fichiersValides.push({ fichier, suivi });
      }
      if (fichiersValides.length === 0) return;
      setFichiers((l) => [...l, ...fichiersValides.map((f) => f.suivi)]);
      // File d'attente séquentielle : le backend traite un fichier à la
      // fois, mieux vaut ne pas paralléliser plusieurs extractions lourdes.
      for (const { fichier, suivi } of fichiersValides) {
        fileQueue.current = fileQueue.current.then(() => traiterFichier(suivi, fichier));
      }
    },
    [traiterFichier, extensionsAutorisees]
  );

  const annulerFichier = useCallback((id: string) => {
    setFichiers((liste) => {
      const cible = liste.find((f) => f.id === id);
      if (cible && cible.statut === "en_cours") cible.controller.abort();
      return liste;
    });
  }, []);

  const retirerFichier = useCallback((id: string) => setFichiers((liste) => liste.filter((f) => f.id !== id)), []);

  const viderListe = useCallback(() => setFichiers([]), []);

  return { fichiers, ajouterFichiers, annulerFichier, retirerFichier, viderListe };
}
