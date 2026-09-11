import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { StatutDocument } from "@/api";

const STATUTS: StatutDocument[] = ["Brouillon", "En cours", "En révision", "Validé", "Final"];

export function statutsAutorises(statut: StatutDocument): StatutDocument[] {
  if (statut === "Final") return [];
  const index = STATUTS.indexOf(statut);
  return [STATUTS[index - 1], STATUTS[index + 1]].filter((valeur): valeur is StatutDocument => valeur !== undefined);
}

interface StatutDocumentBadgeProps {
  statut: StatutDocument;
}

export function StatutDocumentBadge({ statut }: StatutDocumentBadgeProps) {
  const { t } = useTranslation();
  const couleurs: Record<StatutDocument, string> = {
    Brouillon: "border-surface-3 bg-surface-2 text-warmgray",
    "En cours": "border-amethyst-400/30 bg-amethyst-400/10 text-amethyst-400",
    "En révision": "border-gold-600/30 bg-gold-600/10 text-gold-500",
    Validé: "border-risk-low/30 bg-risk-low/10 text-risk-low",
    Final: "border-gold-500/50 bg-gold-500/15 text-gold-500",
  };
  // Le statut reste stocké en base en français (clé stable, voir db.py) --
  // seule sa traduction à l'affichage change avec la langue.
  return <span className={`badge ${couleurs[statut]}`}>{t(`statutDocument.${statut}`)}</span>;
}

interface StatutDocumentMenuProps {
  statut: StatutDocument;
  loading?: boolean;
  onChange: (statut: StatutDocument) => Promise<void> | void;
}

export default function StatutDocumentMenu({ statut, loading = false, onChange }: StatutDocumentMenuProps) {
  const { t } = useTranslation();
  const [valeur, setValeur] = useState("");
  const options = statutsAutorises(statut);

  if (options.length === 0) return null;

  return (
    <select
      className="input h-9 w-auto min-w-40 py-1 text-xs"
      aria-label={t("statutDocument.changerAria", { statut: t(`statutDocument.${statut}`) })}
      value={valeur}
      disabled={loading}
      onChange={(event) => {
        const nouveauStatut = event.target.value as StatutDocument;
        setValeur("");
        void onChange(nouveauStatut);
      }}
    >
      <option value="">{t("statutDocument.changerPlaceholder")}</option>
      {options.map((option) => (
        <option key={option} value={option}>
          {t(`statutDocument.${option}`)}
        </option>
      ))}
    </select>
  );
}