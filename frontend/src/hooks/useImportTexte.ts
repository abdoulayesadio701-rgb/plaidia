/**
 * useImportTexte — import de fichier(s) dans un champ de texte unique
 * (textarea), réutilisé par toutes les pages où l'utilisateur colle ou
 * importe un document (voir "Chantier : import de fichiers partout").
 *
 * Couvre en un seul endroit ce que chaque page reproduisait à la main :
 * - glisser-déposer (props à étaler sur le textarea, `dragProps`) + clic
 *   (via FileDropZone, qui gère déjà son propre bouton) ;
 * - import multiple : chaque fichier est extrait, puis concaténés avec un
 *   séparateur nommant chacun (voir composerTexteCombine) ;
 * - remplacer / ajouter à la suite quand le champ contient déjà du texte
 *   (voir ChoixImportModal, à rendre par la page appelante) ;
 * - erreurs par fichier (format non supporté, trop volumineux, illisible)
 *   remontées en toast, sans jamais bloquer les autres fichiers du lot ni
 *   casser la page.
 *
 * `dossierId` détermine l'endpoint d'extraction utilisé (voir
 * frontend/src/api/dossiers.ts) : fourni -> importerDocument (le texte est
 * aussi ajouté aux faits du dossier) ; null/undefined -> extraireFichier
 * (extraction seule, rien n'est écrit en base) -- pour les pages
 * indépendantes de tout dossier, ou avant même qu'un dossier existe (ex.
 * le formulaire de création).
 */

import { useCallback, useState, type DragEvent } from "react";
import { dossiers as dossiersApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";

export interface ChoixImportEnAttente {
  texte: string;
  noms: string[];
}

interface UseImportTexteOptions {
  dossierId?: number | null;
  /** Lu au moment de l'import (pas de fermeture périmée) pour savoir si le
   * champ contient déjà du texte. */
  getTexteActuel: () => string;
  onTexteExtrait: (texte: string) => void;
}

function composerTexteCombine(extraits: { nom: string; texte: string }[]): string {
  if (extraits.length === 1) return extraits[0].texte;
  return extraits.map((e) => `--- ${e.nom} ---\n${e.texte}`).join("\n\n");
}

export function useImportTexte({ dossierId, getTexteActuel, onTexteExtrait }: UseImportTexteOptions) {
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [enImport, setEnImport] = useState(false);
  const [survole, setSurvole] = useState(false);
  const [choixEnAttente, setChoixEnAttente] = useState<ChoixImportEnAttente | null>(null);

  const appliquer = useCallback(
    (texteExtrait: string, mode: "remplacer" | "ajouter") => {
      const actuel = getTexteActuel();
      onTexteExtrait(mode === "ajouter" && actuel.trim() ? `${actuel}\n\n${texteExtrait}` : texteExtrait);
    },
    [getTexteActuel, onTexteExtrait]
  );

  const importerFichiers = useCallback(
    async (fichiers: FileList | File[]) => {
      const liste = Array.from(fichiers);
      if (liste.length === 0) return;
      setEnImport(true);
      const extraits: { nom: string; texte: string; caracteres: number }[] = [];
      const erreurs: string[] = [];
      for (const fichier of liste) {
        try {
          const resultat = dossierId
            ? await dossiersApi.importerDocument(dossierId, fichier)
            : await dossiersApi.extraireFichier(fichier);
          extraits.push({ nom: resultat.nom_fichier, texte: resultat.texte_extrait, caracteres: resultat.caracteres_extraits });
        } catch (e) {
          erreurs.push(`« ${fichier.name} » : ${e instanceof Error ? e.message : "échec de l'import"}`);
        }
      }
      setEnImport(false);
      if (erreurs.length > 0) pousserToast("error", erreurs.join(" — "));
      if (extraits.length === 0) return;

      const texteCombine = composerTexteCombine(extraits);
      const totalCaracteres = extraits.reduce((s, e) => s + e.caracteres, 0).toLocaleString("fr-FR");
      const noms = extraits.map((e) => e.nom);
      const suffixe = dossierId ? " – également ajouté aux faits du dossier." : "";
      const messageSucces =
        extraits.length > 1
          ? `${extraits.length} fichiers importés (${totalCaracteres} caractères).${suffixe}`
          : `« ${noms[0]} » importé (${totalCaracteres} caractères).${suffixe}`;

      if (getTexteActuel().trim()) {
        setChoixEnAttente({ texte: texteCombine, noms });
      } else {
        appliquer(texteCombine, "remplacer");
        pousserToast("success", messageSucces);
      }
    },
    [dossierId, getTexteActuel, appliquer, pousserToast]
  );

  const resoudreChoix = useCallback(
    (mode: "remplacer" | "ajouter" | "annuler") => {
      if (choixEnAttente && mode !== "annuler") {
        appliquer(choixEnAttente.texte, mode);
        pousserToast("success", `Texte ${mode === "remplacer" ? "remplacé" : "complété"} depuis ${choixEnAttente.noms.join(", ")}.`);
      }
      setChoixEnAttente(null);
    },
    [choixEnAttente, appliquer, pousserToast]
  );

  const dragProps = {
    onDragOver: (e: DragEvent) => {
      e.preventDefault();
      setSurvole(true);
    },
    onDragLeave: () => setSurvole(false),
    onDrop: (e: DragEvent) => {
      e.preventDefault();
      setSurvole(false);
      if (e.dataTransfer.files.length) void importerFichiers(e.dataTransfer.files);
    },
  };

  return { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix };
}
