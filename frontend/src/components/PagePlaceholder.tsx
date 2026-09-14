/**
 * PagePlaceholder — contenu provisoire d'une page pas encore implémentée.
 * Utilisé par toutes les routes déclarées dans navigation.ts en attendant
 * leur page réelle (voir router.tsx) — retirer au fur et à mesure qu'une
 * page reçoit son vrai composant.
 */

import { useTranslation } from "react-i18next";

interface PagePlaceholderProps {
  /** Clé i18next du titre (voir navKey) -- `titleDefault` sert de repli tant qu'aucune traduction n'existe. */
  titleKey: string;
  titleDefault: string;
  description?: string;
}

export default function PagePlaceholder({ titleKey, titleDefault, description }: PagePlaceholderProps) {
  const { t } = useTranslation();
  return (
    <div className="card mx-auto max-w-2xl p-8 text-center">
      <p className="kicker">{t("pagePlaceholder.bientotDisponible")}</p>
      <h1 className="mt-3 font-serif text-h2 font-semibold text-gold-500">{t(titleKey, titleDefault)}</h1>
      {description && <p className="mt-3 text-sm text-warmgray">{description}</p>}
      <p className="mt-6 text-xs text-muted">{t("pagePlaceholder.aVenir")}</p>
    </div>
  );
}
