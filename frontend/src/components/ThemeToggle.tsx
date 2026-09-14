/**
 * ThemeToggle — bascule clair/sombre (soleil/lune), voir useTheme.ts pour
 * la logique. Distinct du lien Paramètres (icône engrenage, TopBar.tsx) :
 * un réglage d'apparence immédiat n'a pas besoin de passer par une page.
 */

import { useTheme } from "@/hooks/useTheme";

export default function ThemeToggle() {
  const { theme, basculerTheme } = useTheme();
  const estSombre = theme === "dark";

  return (
    <button
      onClick={basculerTheme}
      className="rounded-md p-1.5 text-warmgray transition-colors hover:bg-surface-2 hover:text-ivory"
      aria-label={estSombre ? "Passer au thème clair" : "Passer au thème sombre"}
      title={estSombre ? "Thème clair" : "Thème sombre"}
    >
      {estSombre ? (
        // Soleil -- action proposée : repasser au clair
        <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="10" cy="10" r="3.4" />
          <path d="M10 2.5v2M10 15.5v2M17.5 10h-2M4.5 10h-2M15.3 4.7l-1.4 1.4M6.1 13.9l-1.4 1.4M15.3 15.3l-1.4-1.4M6.1 6.1 4.7 4.7" />
        </svg>
      ) : (
        // Lune -- action proposée : passer au sombre
        <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M16.5 12.3A6.8 6.8 0 0 1 7.7 3.5a7 7 0 1 0 8.8 8.8Z" />
        </svg>
      )}
    </button>
  );
}
