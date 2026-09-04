/**
 * ArgumentCard — une carte d'argument analysé (voir /api/analyse/conclusions).
 * Partagée entre AnalyserConclusionsPage et l'onglet "Analyse" de
 * RapportCompletPage plutôt que dupliquée.
 *
 * Chaque champ texte passe par RichOutput plutôt qu'un <p> brut : le
 * fondement, le raisonnement et les pistes de réfutation peuvent tous
 * contenir le marqueur "À VÉRIFIER" (voir le prompt système d'analyse.py),
 * jamais seulement `resume`.
 */

import type { Argument } from "@/api";
import RiskBadge from "./RiskBadge";
import RichOutput from "./RichOutput";
import LabeledField from "./LabeledField";

interface ArgumentCardProps {
  argument: Argument;
  index?: number;
}

export default function ArgumentCard({ argument, index }: ArgumentCardProps) {
  const { resume, fondement, raisonnement, risque, justification_risque, refutations } = argument;

  return (
    <div className="card space-y-4 p-6">
      <div className="flex items-start justify-between gap-4">
        <p className="font-serif text-h4 font-semibold text-ivory">
          {typeof index === "number" && <span className="mr-2 text-warmgray">{index + 1}.</span>}
          {resume}
        </p>
        <RiskBadge risque={risque} className="shrink-0" />
      </div>

      <LabeledField label="Fondement" texte={fondement} />

      {raisonnement && (
        <div className="space-y-3 rounded-md bg-surface-2 p-4">
          <LabeledField label="Problème de droit" texte={raisonnement.probleme_de_droit} />
          <LabeledField label="Règle applicable" texte={raisonnement.regle_applicable} />
          <LabeledField label="Application aux faits" texte={raisonnement.application_aux_faits} />
        </div>
      )}

      <LabeledField label="Conclusion" texte={justification_risque} />

      {refutations.length > 0 && (
        <div>
          <p className="mb-2 text-micro font-medium uppercase tracking-wide text-gold-500">Pistes de réfutation</p>
          <ul className="space-y-2.5">
            {refutations.map((r, i) => (
              <li key={i} className="flex gap-2.5 text-sm">
                <span className="mt-0.5 h-fit shrink-0 rounded-pill border border-gold-600/40 bg-surface-2 px-2 py-0.5 text-micro font-medium text-gold-500">
                  {r.angle}
                </span>
                <RichOutput texte={r.piste} prose={false} className="flex-1" />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
