/**
 * HomePage — écran d'accueil, affiché sur "/". Invite à sélectionner ou
 * créer un dossier, reprend le message d'accueil de gui.py
 * ("Créez ou sélectionnez un dossier ci-dessus pour commencer.").
 */

import { useTranslation } from "react-i18next";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import Logo from "@/components/Logo";

export default function HomePage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const espaceActif = useAppStore((s) => s.espaceActif);

  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-4 py-20 text-center">
      <Logo iconClassName="h-10 w-10 text-gold-500" wordmarkClassName="font-display text-3xl font-bold text-gold-500" />
      {dossierActif ? (
        <>
          <p className="mt-4 text-sm text-warmgray">{t("arsenal.dossierActif")}</p>
          <h1 className="font-serif text-h1 font-semibold text-ivory">{dossierActif.nom}</h1>
          {dossierActif.domaine && <p className="text-sm text-warmgray">{dossierActif.domaine}</p>}
          <p className="mt-4 max-w-prose text-sm text-warmgray">
            {t("home.choisissezAction", { espace: espaceActif === "avocat" ? t("home.espaceAvocat") : t("home.espaceGreffier") })}
          </p>
        </>
      ) : (
        <p className="mt-4 max-w-prose text-sm text-warmgray">
          {t("home.creezOuSelectionnez")}
        </p>
      )}
    </div>
  );
}
