/**
 * EtapePipelineIndicator — indicateur d'étape visible pendant l'attente
 * d'une génération en streaming (chantier "temps de traitement des
 * générations", §3) : remplace un simple spinner par le libellé de l'étape
 * réellement en cours ("Analyse en cours", "Vérification des sources"...),
 * envoyé par le backend au fil de l'eau (évènement SSE "etape", voir
 * frontend/src/hooks/useLazyStream.ts).
 */

import type { EtapePipeline } from "@/api/analyse";

const ICONES: Record<string, string> = {
  garde_fou: "🛡",
  analyse: "🔎",
  verification: "✓",
};

interface EtapePipelineIndicatorProps {
  etape: EtapePipeline | null;
}

export default function EtapePipelineIndicator({ etape }: EtapePipelineIndicatorProps) {
  if (!etape) return null;
  return (
    <div className="card flex items-center gap-3 p-4" role="status" aria-live="polite">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gold-500/30 border-t-gold-500" aria-hidden="true" />
      <span aria-hidden="true">{ICONES[etape.etape] ?? "…"}</span>
      <p className="text-sm text-warmgray">{etape.libelle}</p>
    </div>
  );
}
