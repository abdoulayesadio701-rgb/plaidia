/**
 * StatusBar — reprend self.barre_statut de gui.py : "Prêt" au repos,
 * "⏳ Traitement en cours… (Ns écoulées)" pendant qu'au moins une requête
 * API est en vol (useActivityStore, incrémenté par src/api/http.ts).
 * Porte aussi le pied de page réglementaire (outil d'aide, pas un avis
 * juridique, données non conservées en mode démo) -- toujours visible,
 * pas seulement en mode démo, sur la même ligne pour ne pas alourdir
 * l'interface de travail.
 */

import { useEffect, useState } from "react";
import { useActivityStore } from "@/store/useActivityStore";
import { useAppStore } from "@/store/useAppStore";

export default function StatusBar() {
  const enCours = useActivityStore((s) => s.enCours);
  const depuis = useActivityStore((s) => s.depuis);
  const demoMode = useAppStore((s) => s.demoMode);
  const [maintenant, setMaintenant] = useState(() => Date.now());

  useEffect(() => {
    if (enCours === 0) return;
    const id = window.setInterval(() => setMaintenant(Date.now()), 400);
    return () => window.clearInterval(id);
  }, [enCours]);

  const actif = enCours > 0 && depuis !== null;
  const secondes = actif ? Math.max(0, Math.floor((maintenant - (depuis as number)) / 1000)) : 0;
  const points = ".".repeat((secondes % 3) + 1);

  return (
    <footer className="flex h-8 shrink-0 items-center justify-between gap-4 border-t border-gold-600/15 bg-surface-2/80 px-4 text-xs text-warmgray">
      {actif ? (
        <span>
          ⏳ Traitement en cours{points} <span className="tabular-nums">({secondes}s écoulées)</span>
        </span>
      ) : (
        <span>Prêt</span>
      )}
      <span className="truncate text-muted">
        Plaid'IA est un outil d'aide à la préparation — il ne remplace pas l'analyse d'un avocat.
        {demoMode && " Données non conservées en mode démo."}
      </span>
    </footer>
  );
}
