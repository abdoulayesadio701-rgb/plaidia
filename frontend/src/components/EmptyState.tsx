/**
 * EmptyState — état vide explicite avant toute action (voir consigne
 * "chaque page : état vide explicite"). Distinct de ErrorState : ceci
 * n'est pas un échec, c'est l'invitation à agir.
 */

import type { ReactNode } from "react";

interface EmptyStateProps {
  icone?: ReactNode;
  titre: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export default function EmptyState({ icone, titre, description, action, className = "" }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-gold-600/25 px-6 py-16 text-center ${className}`}>
      {icone && (
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-gold-600/30 bg-surface-2 text-gold-500">
          {icone}
        </div>
      )}
      <h3 className="font-serif text-h4 font-semibold text-ivory">{titre}</h3>
      {description && <p className="max-w-sm text-sm text-warmgray">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
