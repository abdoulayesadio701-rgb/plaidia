/**
 * RiskBadge — pastille de risque (Faible / Moyen / Élevé), voir DESIGN.md §4.
 * Toujours le libellé texte + la couleur, jamais la couleur seule
 * (accessibilité daltonisme).
 */

import type { NiveauRisque } from "@/api";

const CLASSES_PAR_NIVEAU: Record<string, string> = {
  Élevé: "badge-risk-high",
  Moyen: "badge-risk-medium",
  Faible: "badge-risk-low",
};

interface RiskBadgeProps {
  risque: NiveauRisque;
  className?: string;
}

export default function RiskBadge({ risque, className = "" }: RiskBadgeProps) {
  const classe = CLASSES_PAR_NIVEAU[risque] ?? "badge";
  return <span className={`${classe} ${className}`}>{risque}</span>;
}
