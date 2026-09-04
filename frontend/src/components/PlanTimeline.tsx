/**
 * PlanTimeline — accroche, points numérotés en timeline verticale,
 * conclusion, points d'attention. Partagée entre PlanPlaidoiriePage et
 * l'onglet "Plan" de RapportCompletPage.
 */

import type { PlanResultat } from "@/api";
import LabeledField from "./LabeledField";
import RichOutput from "./RichOutput";

interface PlanTimelineProps {
  plan: PlanResultat;
}

export default function PlanTimeline({ plan }: PlanTimelineProps) {
  return (
    <div className="space-y-6">
      <div className="card border-amethyst-400/30 p-6">
        <p className="mb-2 text-micro font-medium uppercase tracking-wide text-amethyst-400">🎤 Accroche</p>
        <RichOutput texte={plan.accroche} />
      </div>

      {plan.plan.length > 0 && (
        <div className="relative space-y-6 border-l-2 border-gold-600/25 pl-8">
          {plan.plan.map((point, i) => (
            <div key={i} className="relative">
              <span className="absolute -left-11 flex h-6 w-6 items-center justify-center rounded-pill border-2 border-gold-600 bg-void font-mono text-xs text-gold-500">
                {i + 1}
              </span>
              <div className="card space-y-3 p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                  <p className="font-serif text-h4 font-semibold text-ivory">{point.point}</p>
                  {point.duree_minutes != null && (
                    <span className="shrink-0 font-mono text-xs text-amethyst-400">{point.duree_minutes} min</span>
                  )}
                </div>
                <LabeledField label="Argument clé" texte={point.argument_cle} />
                <LabeledField label="Notes" texte={point.notes} />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="card border-amethyst-400/30 p-6">
        <p className="mb-2 text-micro font-medium uppercase tracking-wide text-amethyst-400">🎤 Conclusion</p>
        <RichOutput texte={plan.conclusion} />
      </div>

      {plan.points_attention.length > 0 && (
        <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-5">
          <p className="mb-2 text-sm font-semibold text-gold-500">Points d'attention</p>
          <ul className="space-y-1.5">
            {plan.points_attention.map((p, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-gold-500">•</span>
                <RichOutput texte={p} prose={false} className="flex-1 text-sm" />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
