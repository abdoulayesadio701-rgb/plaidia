/**
 * FileDropZone — zone d'import de fichiers réutilisable dans toute l'app.
 * Deux variantes :
 * - "complete" : grande zone en pointillés, glisser-déposer + clic pour
 *   parcourir (voir PreparerDossierPage, le premier endroit où ce
 *   comportement a été construit).
 * - "compact" : simple bouton, pour les pages où l'import est une action
 *   secondaire à côté d'un textarea (Analyser conclusions, Analyse
 *   stylistique, Classement, Extraction, PV d'audience, Cohérence).
 *
 * Ne fait AUCUNE extraction elle-même — purement la sélection de
 * fichier(s) côté navigateur, à combiner avec useImportFichiers (multi-
 * fichiers avec suivi) ou une fonction d'import simple selon le besoin de
 * la page appelante.
 */

import { useRef, useState, type DragEvent, type ReactNode } from "react";
import Button from "./Button";

interface FileDropZoneProps {
  extensions: string[];
  multiple?: boolean;
  disabled?: boolean;
  loading?: boolean;
  onFichiers: (fichiers: FileList) => void;
  variante?: "complete" | "compact";
  titre?: string;
  description?: ReactNode;
  icone?: string;
  libelleBouton?: string;
  className?: string;
}

export default function FileDropZone({
  extensions,
  multiple = false,
  disabled = false,
  loading = false,
  onFichiers,
  variante = "complete",
  titre = "Déposez vos documents ici",
  description,
  icone = "📥",
  libelleBouton = "📎 Importer un fichier",
  className = "",
}: FileDropZoneProps) {
  const [survole, setSurvole] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const accept = extensions.join(",");

  const input = (
    <input
      ref={inputRef}
      type="file"
      multiple={multiple}
      accept={accept}
      className="hidden"
      onChange={(e) => {
        if (e.target.files?.length) onFichiers(e.target.files);
        e.target.value = ""; // permet de réimporter le même fichier deux fois de suite
      }}
    />
  );

  if (variante === "compact") {
    return (
      <>
        {input}
        <Button variant="secondary" loading={loading} disabled={disabled} onClick={() => inputRef.current?.click()} className={className}>
          {libelleBouton}
        </Button>
      </>
    );
  }

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setSurvole(false);
    if (!disabled && e.dataTransfer.files.length) onFichiers(e.dataTransfer.files);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setSurvole(true);
      }}
      onDragLeave={() => setSurvole(false)}
      onDrop={onDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (!disabled && (e.key === "Enter" || e.key === " ")) inputRef.current?.click();
      }}
      className={`flex flex-col items-center gap-3 rounded-md border-2 border-dashed px-6 py-14 text-center transition-colors duration-150 ${
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
      } ${survole ? "border-amethyst-400 bg-amethyst-400/10" : "border-gold-600/30 bg-surface hover:border-gold-500/50"} ${className}`}
    >
      <span className="text-3xl" aria-hidden="true">
        {icone}
      </span>
      <p className="font-serif text-h4 font-semibold text-ivory">{titre}</p>
      {description && <p className="max-w-md text-sm text-warmgray">{description}</p>}
      {input}
    </div>
  );
}
