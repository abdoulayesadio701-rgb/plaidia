/**
 * FullscreenToggle — bascule l'app en plein écran via l'API Fullscreen du
 * navigateur (masque la barre d'adresse/les onglets, utile pour plaider ou
 * présenter l'écran sans distraction). Pas d'équivalent "quitter le
 * programme" : une app web se ferme en fermant l'onglet, voir Logo.tsx pour
 * la même logique de garder l'interface proche du web plutôt que de
 * réintroduire des métaphores de gui.py qui ne s'appliquent plus.
 *
 * Détection de support : Safari iOS ne supporte pas l'API Fullscreen sur
 * <html> -- le bouton se masque silencieusement plutôt que d'échouer au clic.
 */

import { useEffect, useState } from "react";

function pleinEcranSupporte(): boolean {
  return typeof document !== "undefined" && Boolean(document.documentElement.requestFullscreen);
}

export default function FullscreenToggle() {
  const [actif, setActif] = useState(false);
  const [supporte] = useState(pleinEcranSupporte);

  useEffect(() => {
    if (!supporte) return;
    const surChangement = () => setActif(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", surChangement);
    return () => document.removeEventListener("fullscreenchange", surChangement);
  }, [supporte]);

  if (!supporte) return null;

  const basculer = () => {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    } else {
      void document.documentElement.requestFullscreen();
    }
  };

  return (
    <button
      onClick={basculer}
      className="rounded-md p-1.5 text-warmgray transition-colors hover:bg-surface-2 hover:text-ivory"
      aria-label={actif ? "Quitter le plein écran" : "Passer en plein écran"}
      title={actif ? "Quitter le plein écran" : "Plein écran"}
    >
      {actif ? (
        // Quatre coins repliés vers le centre -- "réduire"
        <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M8 3v3a2 2 0 0 1-2 2H3M17 8h-3a2 2 0 0 1-2-2V3M12 17v-3a2 2 0 0 1 2-2h3M3 12h3a2 2 0 0 1 2 2v3" />
        </svg>
      ) : (
        // Quatre coins dépliés vers l'extérieur -- "agrandir"
        <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M3 7V4a1 1 0 0 1 1-1h3M13 3h3a1 1 0 0 1 1 1v3M17 13v3a1 1 0 0 1-1 1h-3M7 17H4a1 1 0 0 1-1-1v-3" />
        </svg>
      )}
    </button>
  );
}
