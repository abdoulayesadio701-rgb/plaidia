/**
 * LandingPage — vitrine publique de Plaid'IA, sur "/" (voir router.tsx).
 * Partageable tel quel (CV, réseaux) : aucun chrome applicatif, pas de
 * dossier requis. Reprend l'atmosphère "grain + lueurs + fenêtre produit"
 * spécifiée pour le hero dans DESIGN.md §4 plutôt qu'une nouvelle identité
 * visuelle ad hoc.
 *
 */

import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { useAppStore } from "@/store/useAppStore";
import Logo from "@/components/Logo";
import Button from "@/components/Button";
import ArgumentCard from "@/components/ArgumentCard";
import SelecteurLangue from "@/components/SelecteurLangue";
import type { Argument } from "@/api";
import justitiaBanniere from "@/assets/justitia-banniere.jpg";
import gardeFouSecurite from "@/assets/garde-fou-securite.jpg";
import gardeFouIntention from "@/assets/garde-fou-intention.jpg";
import gardeFouVerification from "@/assets/garde-fou-verification.jpg";
import gardeFouCritique from "@/assets/garde-fou-critique.jpg";
import gardeFouValidation from "@/assets/garde-fou-validation.jpg";
import {
  IllustrationAnalyser,
  IllustrationChat,
  IllustrationPlan,
  IllustrationSimulateur,
  IllustrationChronologie,
  IllustrationVerification,
} from "@/components/illustrations/FeatureIllustrations";

const URL_GITHUB = "https://github.com/abdoulayesadio701-rgb";
const URL_LINKEDIN = "https://www.linkedin.com/in/abdoulaye-sadio";

function argumentVitrine(t: TFunction): Argument {
  return {
    resume: t("landing.demoArgument.resume"),
    fondement: t("landing.demoArgument.fondement"),
    raisonnement: {
      probleme_de_droit: t("landing.demoArgument.problemeDeDroit"),
      regle_applicable: t("landing.demoArgument.regleApplicable"),
      application_aux_faits: t("landing.demoArgument.applicationAuxFaits"),
    },
    risque: "Moyen",
    justification_risque: t("landing.demoArgument.justificationRisque"),
    refutations: [
      { angle: t("landing.demoArgument.refutation1Angle"), piste: t("landing.demoArgument.refutation1Piste") },
      { angle: t("landing.demoArgument.refutation2Angle"), piste: t("landing.demoArgument.refutation2Piste") },
    ],
  };
}

function fonctionnalites(t: TFunction) {
  return [
    {
      Illustration: IllustrationAnalyser,
      titre: t("nav.arsenal.analyser"),
      description: t("landing.descAnalyser"),
      lien: "/app/arsenal/analyser",
    },
    {
      Illustration: IllustrationChat,
      titre: t("nav.chat"),
      description: t("landing.descChat"),
      lien: "/app/chat",
    },
    {
      Illustration: IllustrationPlan,
      titre: t("landing.titrePlan"),
      description: t("landing.descPlan"),
      lien: "/app/arsenal/plan",
    },
    {
      Illustration: IllustrationSimulateur,
      titre: t("nav.arsenal.simulateur"),
      description: t("landing.descSimulateur"),
      lien: "/app/arsenal/simulateur",
    },
    {
      Illustration: IllustrationChronologie,
      titre: t("landing.titreChronologie"),
      description: t("landing.descChronologie"),
      lien: "/app/greffier/chronologie",
    },
    {
      Illustration: IllustrationVerification,
      titre: t("nav.arsenal.verification-procedurale"),
      description: t("landing.descVerification"),
      lien: "/app/arsenal/verification-procedurale",
    },
  ];
}

function etapes(t: TFunction) {
  return [
    { numero: "01", titre: t("landing.etape1Titre"), description: t("landing.etape1Description") },
    { numero: "02", titre: t("landing.etape2Titre"), description: t("landing.etape2Description") },
    { numero: "03", titre: t("landing.etape3Titre"), description: t("landing.etape3Description") },
  ];
}

export default function LandingPage() {
  const { t } = useTranslation();
  const FONCTIONNALITES = fonctionnalites(t);
  const ETAPES = etapes(t);
  const ARGUMENT_VITRINE = argumentVitrine(t);
  const navigate = useNavigate();
  const chargerConfiguration = useAppStore((s) => s.chargerConfiguration);
  const demoMode = useAppStore((s) => s.demoMode);

  useEffect(() => {
    // Précharge l'état démo pour que le bandeau de AppLayout n'apparaisse
    // pas avec un temps de retard visible juste après le clic "Essayer".
    void chargerConfiguration();
  }, [chargerConfiguration]);

  const essayerLaDemo = () => navigate("/app/chemise/dossiers");

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-void text-ivory">
      <div className="grain" aria-hidden="true" />

      {/* --- Nav ------------------------------------------------------ */}
      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-6">
        <Logo />
        <nav className="hidden items-center gap-6 text-sm text-warmgray md:flex">
          <a href="#fonctionnalites" className="transition-colors hover:text-ivory">
            {t("landing.navFonctionnalites")}
          </a>
          <a href="#comment-ca-marche" className="transition-colors hover:text-ivory">
            {t("landing.navCommentCaMarche")}
          </a>
          <a href="#garde-fou" className="transition-colors hover:text-ivory">
            {t("landing.navVerification")}
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <SelecteurLangue />
          <a
            href={URL_GITHUB}
            target="_blank"
            rel="noreferrer"
            className="hidden text-warmgray transition-colors hover:text-ivory sm:inline-flex"
            aria-label={t("landing.codeSourceGithub")}
            title="GitHub"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
              <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.09 3.29 9.4 7.86 10.93.58.1.79-.25.79-.56 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.56-.29-5.26-1.28-5.26-5.69 0-1.26.45-2.29 1.18-3.09-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.05 11.05 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.24 2.76.12 3.05.74.8 1.18 1.83 1.18 3.09 0 4.42-2.71 5.4-5.28 5.68.42.36.78 1.08.78 2.17 0 1.56-.01 2.82-.01 3.2 0 .31.2.67.8.56A10.52 10.52 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
            </svg>
          </a>
          <Button variant="primary" onClick={essayerLaDemo}>
            {t("landing.essayerDemo")}
          </Button>
        </div>
      </header>

      {/* --- Hero ------------------------------------------------------ */}
      <section className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-14 px-6 pb-24 pt-8 lg:grid-cols-[1.05fr_1fr] lg:pb-32">
        <div className="glow -left-24 top-0 h-72 w-72 bg-gold-600/20" aria-hidden="true" />
        <div className="glow -right-24 top-40 h-80 w-80 bg-amethyst-600/25" aria-hidden="true" />

        <div className="relative z-10 space-y-6">
          <p className="kicker">{t("landing.kicker")}</p>
          <h1 className="font-display text-4xl font-bold leading-[1.1] text-gold-500 sm:text-5xl">
            {t("landing.titre1")}
            <br />
            {t("landing.titre2")}
          </h1>
          <p className="max-w-prose text-base leading-relaxed text-warmgray sm:text-lg">
            {t("landing.description")}
          </p>
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Button variant="primary" onClick={essayerLaDemo}>
              {t("landing.essayerDemo")}
            </Button>
            <a href={URL_GITHUB} target="_blank" rel="noreferrer" className="btn-secondary">
              {t("landing.voirCodeGithub")}
            </a>
          </div>
          {demoMode && (
            <p className="text-xs text-muted">
              🎭 {t("landing.modeDemo")}
            </p>
          )}
        </div>

        {/* Fenêtre produit -- la thèse visuelle, pas un fond abstrait (DESIGN.md §4) */}
        <div className="relative z-10">
          <div className="window">
            <div className="window-bar">
              <span className="window-dot" />
              <span className="window-dot" />
              <span className="window-dot" />
              <span className="ml-2 text-xs text-warmgray">{t("nav.arsenal.analyser")}</span>
            </div>
                <div className="window-content">
                  <ArgumentCard argument={ARGUMENT_VITRINE} index={0} />
                  <div className="window-content-fade" aria-hidden="true" />
            </div>
          </div>
        </div>
      </section>

      {/* --- Fonctionnalités -------------------------------------------- */}
      <section id="fonctionnalites" className="relative mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="kicker mx-auto">{t("landing.ceQueFaitLoutil")}</p>
          <h2 className="mt-2 font-serif text-h1 font-semibold text-gold-500">{t("landing.sixEspaces")}</h2>
        </div>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FONCTIONNALITES.map((f) => (
            // Carte réellement cliquable -- mène à l'espace de travail
            // correspondant (voir src/config/navigation.ts pour la
            // correspondance path/requiresDossier). Le survol (zoom léger
            // de l'illustration) existait déjà avant que la carte ne mène
            // quelque part ; il devient enfin cohérent avec ce qu'il
            // suggère.
            <Link key={f.titre} to={f.lien} className="card group overflow-hidden !p-0">
              <div className="relative aspect-[8/5] overflow-hidden border-b border-gold-600/15 bg-gradient-to-br from-surface-2 to-surface">
                <f.Illustration className="absolute inset-0 h-full w-full p-7 text-amethyst-600/70 transition-transform duration-300 ease-out group-hover:scale-[1.04]" />
              </div>
              <div className="space-y-3 p-6">
                <h3 className="font-serif text-h3 font-semibold text-ivory">{f.titre}</h3>
                <p className="text-sm leading-relaxed text-warmgray">{f.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* --- Comment ça marche ------------------------------------------- */}
      <section id="comment-ca-marche" className="relative mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="kicker mx-auto">{t("landing.priseEnMain")}</p>
          <h2 className="mt-2 font-serif text-h1 font-semibold text-gold-500">{t("landing.navCommentCaMarche")}</h2>
        </div>
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          {ETAPES.map((e) => (
            <div key={e.numero} className="relative space-y-3 border-t-2 border-gold-600/40 pt-5">
              <span className="font-mono text-sm text-amethyst-400">{e.numero}</span>
              <h3 className="font-serif text-h3 font-semibold text-ivory">{e.titre}</h3>
              <p className="text-sm leading-relaxed text-warmgray">{e.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* --- Bandeau photographique --------------------------------------- */}
      <section className="banner-photo">
        <img src={justitiaBanniere} alt={t("landing.altJustitia")} />
        <div className="banner-scrim" aria-hidden="true" />
        <div className="banner-wash" aria-hidden="true" />
        <div className="banner-edgefade" aria-hidden="true" />
        <div className="relative z-10 mx-auto w-full max-w-6xl px-6 sm:px-10">
          <p className="kicker">{t("landing.ceQueLoutilNeFeraJamais")}</p>
          <h2 className="mt-3 max-w-xl font-display text-3xl font-bold leading-tight text-ivory sm:text-4xl">
            {t("landing.peserChaqueArgument")}
            <br />
            <span className="text-gold-500">{t("landing.jamaisTrancher")}</span>
          </h2>
        </div>
      </section>

      {/* --- Garde-fou anti-hallucination : architecture multi-agents ----- */}
      <section id="garde-fou" className="relative mx-auto max-w-5xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="kicker mx-auto">{t("landing.plusieursGardeFous")}</p>
          <h2 className="mt-2 font-serif text-h1 font-semibold text-gold-500">{t("landing.verifierAvantAffirmer")}</h2>
          <p className="mx-auto mt-4 max-w-prose text-sm leading-relaxed text-warmgray sm:text-base">
            {t("landing.gardeFouIntro1")}{" "}
            <mark className="marker-verify">{t("richOutput.aVerifier")} : ...</mark> {t("landing.gardeFouIntro2")}
          </p>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {[
            {
              icone: "🛡",
              titre: t("landing.etapeSecuriteTitre"),
              texte: t("landing.etapeSecuriteTexte"),
              photo: gardeFouSecurite,
              photoAlt: t("landing.etapeSecuritePhotoAlt"),
            },
            {
              icone: "🎯",
              titre: t("landing.etapeIntentionTitre"),
              texte: t("landing.etapeIntentionTexte"),
              photo: gardeFouIntention,
              photoAlt: t("landing.etapeIntentionPhotoAlt"),
            },
            {
              icone: "📚",
              titre: t("landing.etapeVerifJuridiqueTitre"),
              texte: t("landing.etapeVerifJuridiqueTexte"),
              photo: gardeFouVerification,
              photoAlt: t("landing.etapeVerifJuridiquePhotoAlt"),
            },
            {
              icone: "⚖",
              titre: t("landing.etapeCritiqueTitre"),
              texte: t("landing.etapeCritiqueTexte"),
              photo: gardeFouCritique,
              photoAlt: t("landing.etapeCritiquePhotoAlt"),
            },
            {
              icone: "✓",
              titre: t("landing.etapeValidationTitre"),
              texte: t("landing.etapeValidationTexte"),
              photo: gardeFouValidation,
              photoAlt: t("landing.etapeValidationPhotoAlt"),
            },
          ].map((etape) => (
            <div
              key={etape.titre}
              className={`card overflow-hidden space-y-2 p-5 text-center ${!etape.photo ? "flex h-full flex-col justify-center" : ""}`}
            >
              {etape.photo && (
                <div className="relative -mx-5 -mt-5 mb-1 aspect-[4/3] overflow-hidden">
                  <img src={etape.photo} alt={etape.photoAlt} className="h-full w-full object-cover" loading="lazy" />
                  <div className="absolute inset-0 bg-gradient-to-t from-amethyst-700/80 via-amethyst-700/10 to-transparent" aria-hidden="true" />
                  <p className="absolute bottom-2 left-1/2 -translate-x-1/2 text-2xl" aria-hidden="true">
                    {etape.icone}
                  </p>
                </div>
              )}
              {!etape.photo && (
                <p className="text-2xl" aria-hidden="true">
                  {etape.icone}
                </p>
              )}
              <p className="text-sm font-semibold text-ivory">{etape.titre}</p>
              <p className="text-xs leading-relaxed text-warmgray">{etape.texte}</p>
            </div>
          ))}
        </div>

        <p className="mx-auto mt-8 max-w-prose text-center text-xs leading-relaxed text-muted sm:text-sm">
          {t("landing.gardeFouOutro")}
        </p>
      </section>

      {/* --- Footer ------------------------------------------------------- */}
      <footer className="relative border-t border-gold-600/15 bg-surface/60">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="grid grid-cols-1 gap-10 sm:grid-cols-3">
            <div className="space-y-3">
              <Logo iconClassName="h-6 w-6 text-gold-500" wordmarkClassName="font-display text-lg font-bold text-gold-500" />
              <p className="max-w-xs text-sm text-warmgray">
                {t("landing.footerAssistant")}
              </p>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-micro font-medium uppercase tracking-wide text-warmgray">{t("landing.leProduit")}</p>
              <a href="#fonctionnalites" className="block text-ivory hover:text-gold-500">
                {t("landing.navFonctionnalites")}
              </a>
              <a href="#comment-ca-marche" className="block text-ivory hover:text-gold-500">
                {t("landing.navCommentCaMarche")}
              </a>
              <Link to="/app/chemise/dossiers" className="block text-ivory hover:text-gold-500">
                {t("landing.essayerDemoSansFleche")}
              </Link>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-micro font-medium uppercase tracking-wide text-warmgray">{t("landing.contact")}</p>
              <a href={URL_GITHUB} target="_blank" rel="noreferrer" className="block text-ivory hover:text-gold-500">
                GitHub
              </a>
              <a href={URL_LINKEDIN} target="_blank" rel="noreferrer" className="block text-ivory hover:text-gold-500">
                LinkedIn
              </a>
              <p className="pt-1 text-xs text-muted">{t("landing.projetPortfolio")}</p>
            </div>
          </div>

          <div className="mt-10 border-t border-gold-600/10 pt-6 text-center text-xs text-muted">
            {t("statusBar.avertissement")} {t("landing.aucuneDonneeDemo")}
          </div>
        </div>
      </footer>
    </div>
  );
}
