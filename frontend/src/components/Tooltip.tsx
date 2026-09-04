/**
 * Tooltip — infobulle légère en CSS pur (pas de librairie), utilisée
 * notamment par Sidebar pour expliquer pourquoi une action est désactivée
 * ("Sélectionnez un dossier pour activer cette action").
 */

import type { ReactNode } from "react";

interface TooltipProps {
  label: string;
  children: ReactNode;
  className?: string;
}

export default function Tooltip({ label, children, className = "" }: TooltipProps) {
  return (
    <span className={`group/tooltip relative inline-flex ${className}`}>
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 w-max max-w-[220px] -translate-x-1/2 rounded-md border border-gold-600/30 bg-surface-2 px-2.5 py-1.5 text-center text-xs text-ivory opacity-0 shadow-card transition-opacity duration-150 group-hover/tooltip:opacity-100"
      >
        {label}
      </span>
    </span>
  );
}
