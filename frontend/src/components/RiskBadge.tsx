/**
 * RiskBadge — pastille de risque (Faible / Moyen / Élevé), voir DESIGN.md §4.
 * Toujours le libellé texte + la couleur, jamais la couleur seule
 * (accessibilité daltonisme).
 */

import { useTranslation } from "react-i18next";
import type { NiveauRisque } from "@/api";

const CLASSES_PAR_NIVEAU: Record<string, string> = {
  Élevé: "badge-risk-high",
  Moyen: "badge-risk-medium",
  Faible: "badge-risk-low",
};

interface RiskBadgeProps {
  /** Valeur fixe renvoyée par le backend (analyse.py) -- toujours l'un de
   * ces trois tokens français, quelle que soit la langue de l'interface
   * (voir schémas JSON de analyse.py). */
  risque: NiveauRisque;
  className?: string;
}

export default function RiskBadge({ risque, className = "" }: RiskBadgeProps) {
  const { t } = useTranslation();
  const classe = CLASSES_PAR_NIVEAU[risque] ?? "badge";
  return <span className={`${classe} ${className}`}>{t(`niveauRisque.${risque}`, risque)}</span>;
}
