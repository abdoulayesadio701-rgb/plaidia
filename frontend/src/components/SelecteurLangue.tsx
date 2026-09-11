/**
 * SelecteurLangue — bascule FR/EN de la barre de tâches (voir "Chantier :
 * internationalisation français / anglais", étape 1). Applique la langue
 * immédiatement (i18next re-rend tout composant utilisant useTranslation(),
 * aucun rechargement de page) et la persiste en localStorage via
 * definirLangue (voir frontend/src/i18n) -- français par défaut.
 */

import { useTranslation } from "react-i18next";
import { definirLangue, LANGUES_SUPPORTEES, type Langue } from "@/i18n";

export default function SelecteurLangue() {
  const { t, i18n } = useTranslation();
  const langueActive = (i18n.language || "fr") as Langue;

  return (
    <div className="flex shrink-0 items-center rounded-md border border-gold-600/20 bg-surface-2 p-0.5 text-xs" role="group" aria-label={t("langue.selecteurAria")}>
      {LANGUES_SUPPORTEES.map((langue) => (
        <button
          key={langue}
          type="button"
          onClick={() => definirLangue(langue)}
          aria-pressed={langueActive === langue}
          className={`rounded-md px-2 py-1 font-semibold transition-colors ${
            langueActive === langue ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:text-ivory"
          }`}
        >
          {t(`langue.${langue}`)}
        </button>
      ))}
    </div>
  );
}
