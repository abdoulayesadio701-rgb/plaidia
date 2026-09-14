/**
 * useTheme — bascule clair/sombre. Pose/retire la classe "dark" sur
 * <html> (seule chose que globals.css regarde pour choisir entre les
 * tokens :root et .dark, voir §Thème sombre) et persiste le choix en
 * localStorage pour les visites suivantes.
 *
 * L'état initial est lu directement sur le DOM plutôt que recalculé
 * depuis localStorage : le script inline de index.html a déjà posé la
 * classe avant le premier rendu React (évite un flash du thème clair par
 * défaut le temps que ce hook se monte) -- ce hook ne fait que refléter
 * ce choix déjà appliqué, puis le faire évoluer.
 */

import { useCallback, useState } from "react";

const CLE_STOCKAGE = "plaidia-theme";

export type Theme = "light" | "dark";

function themeInitial(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(themeInitial);

  const basculerTheme = useCallback(() => {
    setTheme((actuel) => {
      const suivant: Theme = actuel === "dark" ? "light" : "dark";
      document.documentElement.classList.toggle("dark", suivant === "dark");
      try {
        localStorage.setItem(CLE_STOCKAGE, suivant);
      } catch {
        // Navigation privée / stockage désactivé -- le choix ne survivra
        // pas à cette session, mais le toggle continue de fonctionner.
      }
      return suivant;
    });
  }, []);

  return { theme, basculerTheme };
}
