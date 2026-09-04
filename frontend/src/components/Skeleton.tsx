/**
 * Skeleton — blocs pulsants pendant le chargement, à composer pour
 * suggérer la forme du contenu à venir (une carte d'argument, une ligne de
 * texte...) plutôt qu'un simple spinner générique.
 */

interface SkeletonBlockProps {
  className?: string;
}

export function SkeletonBlock({ className = "h-4 w-full" }: SkeletonBlockProps) {
  return <div className={`animate-pulse rounded-md bg-surface-3 ${className}`} />;
}

/** Silhouette d'une carte de résultat (titre + 2-3 lignes) — le cas le plus fréquent. */
export function SkeletonCard() {
  return (
    <div className="card space-y-3 p-6">
      <SkeletonBlock className="h-5 w-2/3" />
      <SkeletonBlock className="h-3.5 w-full" />
      <SkeletonBlock className="h-3.5 w-5/6" />
      <SkeletonBlock className="h-3.5 w-4/6" />
    </div>
  );
}

interface SkeletonListProps {
  count?: number;
}

export function SkeletonList({ count = 3 }: SkeletonListProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
