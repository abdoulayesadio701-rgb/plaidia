/**
 * JaugeConfiance — jauge de confiance (Élevée / Moyenne / Faible, voir
 * analyse.py::classifier_document). Sémantique inverse de RiskBadge :
 * ici "Élevée" est une bonne nouvelle (vert), "Faible" une mauvaise
 * (rouge) -- d'où un composant dédié plutôt qu'une réutilisation de
 * RiskBadge, dont les couleurs vont dans l'autre sens.
 */

import { useTranslation } from "react-i18next";

interface NiveauConfig {
  pourcentage: number;
  classeBarre: string;
  classeTexte: string;
}

const NIVEAUX: Record<string, NiveauConfig> = {
  Élevée: { pourcentage: 100, classeBarre: "bg-risk-low", classeTexte: "text-risk-low" },
  Moyenne: { pourcentage: 60, classeBarre: "bg-risk-medium", classeTexte: "text-risk-medium" },
  Faible: { pourcentage: 25, classeBarre: "bg-risk-high", classeTexte: "text-risk-high" },
};

const NIVEAU_INCONNU: NiveauConfig = { pourcentage: 10, classeBarre: "bg-muted", classeTexte: "text-muted" };

interface JaugeConfianceProps {
  /** Valeur fixe renvoyée par le backend (analyse.py) -- toujours l'un de
   * ces trois tokens français, quelle que soit la langue de l'interface
   * (voir schémas JSON de analyse.py) ; NIVEAUX_LABEL en donne l'affichage
   * traduit. */
  niveau: string;
  label?: string;
}

export default function JaugeConfiance({ niveau, label }: JaugeConfianceProps) {
  const { t } = useTranslation();
  const config = NIVEAUX[niveau] ?? NIVEAU_INCONNU;
  const niveauAffiche = t(`niveauConfiance.${niveau}`, niveau);
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="text-micro font-medium uppercase tracking-wide text-warmgray">{label ?? t("jaugeConfiance.label")}</span>
        <span className={`text-sm font-semibold ${config.classeTexte}`}>{niveauAffiche}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-pill bg-surface-3">
        <div
          className={`h-full rounded-pill transition-all duration-500 ${config.classeBarre}`}
          style={{ width: `${config.pourcentage}%` }}
        />
      </div>
    </div>
  );
}
