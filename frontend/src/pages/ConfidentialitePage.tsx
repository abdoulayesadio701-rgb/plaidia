/**
 * ConfidentialitePage — /confidentialite. Page légale autonome (hors
 * AppLayout, comme LandingPage) : où vont les données saisies dans
 * Plaid'IA, ce qui est optionnel, ce que fait l'option d'anonymisation des
 * noms (voir AnalyserConclusionsPage.tsx) et les limites honnêtes du
 * projet. Accessible depuis le footer de la landing et, en nouvel onglet,
 * depuis la case à cocher "Anonymiser" de l'Arsenal.
 */

import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Logo from "@/components/Logo";

function Section({ titre, children }: { titre: string; children: ReactNode }) {
  return (
    <section className="border-t border-gold-600/15 pt-8">
      <h2 className="font-serif text-h3 font-semibold text-gold-500">{titre}</h2>
      <div className="mt-3 space-y-3 text-sm leading-relaxed text-warmgray">{children}</div>
    </section>
  );
}

export default function ConfidentialitePage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-gold-600/15">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-5">
          <Link to="/" className="flex items-center gap-2">
            <Logo iconClassName="h-6 w-6 text-gold-500" wordmarkClassName="font-display text-lg font-bold text-gold-500" />
          </Link>
          <Link to="/" className="text-xs font-medium text-warmgray hover:text-ivory">
            {t("confidentialite.retourAccueil")}
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-8 px-6 py-12">
        <div>
          <p className="kicker">{t("confidentialite.kicker")}</p>
          <h1 className="mt-1 font-serif text-h1 font-semibold text-ivory">{t("confidentialite.titre")}</h1>
          <p className="mt-3 text-sm text-warmgray">{t("confidentialite.chapeau")}</p>
        </div>

        <Section titre={t("confidentialite.donnees.titre")}>
          <p>{t("confidentialite.donnees.intro")}</p>
          <ul className="list-disc space-y-2 pl-5">
            <li>{t("confidentialite.donnees.anthropic")}</li>
            <li>{t("confidentialite.donnees.deepseek")}</li>
            <li>{t("confidentialite.donnees.judilibre")}</li>
            <li>{t("confidentialite.donnees.aucunAutre")}</li>
          </ul>
        </Section>

        <Section titre={t("confidentialite.entrainement.titre")}>
          <p>{t("confidentialite.entrainement.texte")}</p>
        </Section>

        <Section titre={t("confidentialite.modeDemo.titre")}>
          <p>{t("confidentialite.modeDemo.texte")}</p>
        </Section>

        <Section titre={t("confidentialite.clePersonnelle.titre")}>
          <p>{t("confidentialite.clePersonnelle.texte")}</p>
        </Section>

        <Section titre={t("confidentialite.anonymisation.titre")}>
          <p>{t("confidentialite.anonymisation.texte1")}</p>
          <p>{t("confidentialite.anonymisation.texte2")}</p>
          <p className="italic">{t("confidentialite.anonymisation.limite")}</p>
        </Section>

        <Section titre={t("confidentialite.jurisprudence.titre")}>
          <p>{t("confidentialite.jurisprudence.texte")}</p>
        </Section>

        <Section titre={t("confidentialite.perimetre.titre")}>
          <p>{t("confidentialite.perimetre.texte1")}</p>
          <p>{t("confidentialite.perimetre.texte2")}</p>
        </Section>

        <Section titre={t("confidentialite.contact.titre")}>
          <p>{t("confidentialite.contact.texte")}</p>
        </Section>

        <p className="border-t border-gold-600/15 pt-6 text-xs text-muted">{t("confidentialite.derniereMaj")}</p>
      </main>
    </div>
  );
}
