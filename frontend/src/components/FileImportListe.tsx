/**
 * FileImportListe — liste des fichiers en cours/déjà importés, avec
 * statut, taille, caractères extraits, barre de progression et actions
 * (annuler/retirer). Rendu associé à useImportFichiers — voir
 * PreparerDossierPage, le premier endroit où cette liste a été construite.
 */

import type { FichierSuivi } from "@/hooks/useImportFichiers";
import { formaterTailleFichier } from "@/config/fichiers";

interface FileImportListeProps {
  fichiers: FichierSuivi[];
  onAnnuler: (id: string) => void;
  onRetirer: (id: string) => void;
  onVider?: () => void;
}

export default function FileImportListe({ fichiers, onAnnuler, onRetirer, onVider }: FileImportListeProps) {
  if (fichiers.length === 0) return null;
  const nombreTermines = fichiers.filter((f) => f.statut === "termine").length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-warmgray">
          {nombreTermines}/{fichiers.length} document{fichiers.length > 1 ? "s" : ""} importé{nombreTermines > 1 ? "s" : ""}
        </p>
        {onVider && (
          <button onClick={onVider} className="text-xs text-muted hover:text-warmgray">
            Vider la liste
          </button>
        )}
      </div>
      <ul className="space-y-2.5">
        {fichiers.map((f) => (
          <li key={f.id} className="card space-y-2 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-ivory">{f.nom}</p>
                <p className="text-xs text-muted">
                  {formaterTailleFichier(f.taille)}
                  {f.statut === "termine" && f.caracteresExtraits != null && ` · ${f.caracteresExtraits.toLocaleString("fr-FR")} caractères extraits`}
                  {f.statut === "erreur" && f.erreur && <span className="text-risk-high"> · {f.erreur}</span>}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {f.statut === "termine" && <span className="text-lg text-risk-low">✓</span>}
                {f.statut === "erreur" && <span className="text-lg text-risk-high">⚠</span>}
                {f.statut === "en_cours" && (
                  <button onClick={() => onAnnuler(f.id)} className="text-xs text-warmgray hover:text-ivory">
                    Annuler
                  </button>
                )}
                {f.statut !== "en_cours" && (
                  <button onClick={() => onRetirer(f.id)} className="text-xs text-muted hover:text-ivory" aria-label={`Retirer ${f.nom} de la liste`}>
                    ✕
                  </button>
                )}
              </div>
            </div>
            {(f.statut === "en_cours" || f.statut === "en_attente") && (
              <div className="h-1.5 w-full overflow-hidden rounded-pill bg-surface-3">
                <div
                  className="h-full rounded-pill bg-amethyst-400 transition-all duration-200"
                  style={{ width: `${f.statut === "en_attente" ? 0 : f.progression}%` }}
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
