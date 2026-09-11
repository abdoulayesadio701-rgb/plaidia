/**
 * LabeledField — petite légende en majuscules au-dessus d'un texte rendu
 * via RichOutput (donc avec rendu dédié des balises [ART:...]/
 * [JURISPRUDENCE:...]/[VERIF:...]). Motif répété dans ArgumentCard,
 * PlanPlaidoiriePage, SimulateurObjectionsPage... — un seul endroit pour
 * le faire correctement plutôt que copié partout.
 */

import RichOutput from "./RichOutput";

interface LabeledFieldProps {
  label: string;
  texte: string;
  className?: string;
}

export default function LabeledField({ label, texte, className = "" }: LabeledFieldProps) {
  if (!texte) return null;
  return (
    <div className={className}>
      <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">{label}</p>
      <RichOutput texte={texte} prose={false} className="text-sm" />
    </div>
  );
}
