/**
 * RechercheDossierResultats — rendu partagé d'une recherche transversale
 * (extraits surlignés dans faits/parties/nom/domaine/analyses). Utilisé par
 * DossiersPage (La Chemise, recherche parmi "mes" dossiers) et
 * RechercheTransversalePage (Le Greffier, recherche dans "toutes les
 * affaires") -- même forme de résultat des deux côtés puisque les deux
 * routes appellent finalement db.py::rechercher_dans_dossiers.
 */

import type { RechercheDossierResultat } from "@/api";
import EmptyState from "./EmptyState";
import ErrorState from "./ErrorState";
import { SkeletonBlock } from "./Skeleton";

const LABELS_CHAMP: Record<string, string> = {
  nom: "Nom",
  domaine: "Domaine",
  faits: "Faits",
  parties: "Parties",
};

/** Met en évidence les occurrences du terme recherché dans un extrait. */
function surlignerExtrait(extrait: string, terme: string) {
  if (!terme.trim()) return extrait;
  const parts = extrait.split(new RegExp(`(${terme.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"));
  return parts.map((part, i) =>
    part.toLowerCase() === terme.toLowerCase() ? (
      <mark key={i} className="marker-verify">
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

interface RechercheDossierResultatsProps {
  resultats: RechercheDossierResultat[] | null;
  loading: boolean;
  erreur: string | null;
  terme: string;
  onRelancer: () => void;
  onOuvrir: (id: number) => void;
}

export default function RechercheDossierResultats({ resultats, loading, erreur, terme, onRelancer, onOuvrir }: RechercheDossierResultatsProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="card space-y-2.5 p-5">
            <SkeletonBlock className="h-4 w-1/3" />
            <SkeletonBlock className="h-3.5 w-full" />
          </div>
        ))}
      </div>
    );
  }
  if (erreur) return <ErrorState message={erreur} onRetry={onRelancer} />;
  if (!resultats || resultats.length === 0) {
    return <EmptyState titre="Aucun résultat" description={`Aucun dossier ne correspond à « ${terme} ».`} />;
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-warmgray">
        {resultats.length} dossier{resultats.length > 1 ? "s" : ""} correspondant{resultats.length > 1 ? "s" : ""} à « {terme} »
      </p>
      {resultats.map(({ dossier, extraits }) => (
        <div
          key={dossier.id}
          className="card-interactive space-y-2.5 p-5"
          onClick={() => onOuvrir(dossier.id)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onOuvrir(dossier.id);
            }
          }}
          role="button"
          tabIndex={0}
        >
          <div className="flex items-center justify-between gap-3">
            <p className="font-serif text-h4 font-semibold text-ivory">{dossier.nom}</p>
            {dossier.domaine && <span className="badge border-gold-600/30 bg-surface-2 text-warmgray">{dossier.domaine}</span>}
          </div>
          <ul className="space-y-1.5">
            {extraits.map(([champ, extrait], i) => (
              <li key={i} className="text-sm text-warmgray">
                <span className="mr-1.5 text-micro font-medium uppercase tracking-wide text-amethyst-400">
                  {LABELS_CHAMP[champ] ?? champ}
                </span>
                {surlignerExtrait(extrait, terme)}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
