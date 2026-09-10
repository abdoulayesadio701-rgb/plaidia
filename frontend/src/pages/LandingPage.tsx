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
import { useAppStore } from "@/store/useAppStore";
import Logo from "@/components/Logo";
import Button from "@/components/Button";
import ArgumentCard from "@/components/ArgumentCard";
import type { Argument } from "@/api";
import justitiaBanniere from "@/assets/justitia-banniere.jpg";
import gardeFouSecurite from "@/assets/garde-fou-securite.jpg";
import gardeFouIntention from "@/assets/garde-fou-intention.jpg";
import gardeFouVerification from "@/assets/garde-fou-verification.jpg";
import gardeFouCritique from "@/assets/garde-fou-critique.jpg";
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

const ARGUMENT_VITRINE: Argument = {
  resume: "Les trois retards des 5, 8 et 9 février 2024 caractérisent un manquement réitéré à l'obligation de ponctualité.",
  fondement: "Relevé de badgeuse produit en pièce 4 par l'employeur, faisant état de trois retards de 22 à 41 minutes.",
  raisonnement: {
    probleme_de_droit: "Des retards répétés, même de courte durée, peuvent-ils à eux seuls caractériser une faute grave ?",
    regle_applicable: "La faute grave suppose un manquement rendant impossible le maintien du salarié dans l'entreprise pendant le préavis. À VÉRIFIER : la qualification retenue pour des retards isolés sans avertissement préalable.",
    application_aux_faits: "M. Diallo n'a fait l'objet d'aucune sanction en cinq ans d'ancienneté ; les retards coïncident avec un mouvement de grève RER B (pièce 7), ce qui affaiblit le caractère fautif retenu par l'employeur.",
  },
  risque: "Moyen",
  justification_risque: "L'absence d'antécédent et la coïncidence avec la grève fragilisent la qualification de faute grave, sans l'exclure totalement.",
  refutations: [
    { angle: "Factuel", piste: "Produire l'attestation SNCF de perturbation du trafic aux dates visées." },
    { angle: "Juridique", piste: "À VÉRIFIER : rechercher un arrêt excluant la faute grave en cas de grève des transports." },
  ],
};

const FONCTIONNALITES = [
  {
    Illustration: IllustrationAnalyser,
    titre: "Analyser des conclusions adverses",
    description: "Chaque argument décomposé en syllogisme – problème de droit, règle applicable, application aux faits – avec niveau de risque et pistes de réfutation.",
  },
  {
    Illustration: IllustrationChat,
    titre: "Chat juridique",
    description: "Posez une question précise, obtenez une réponse structurée appuyée sur la juridiction active — avec, sur les questions les plus sensibles, une vérification multi-agents avant l'affichage.",
  },
  {
    Illustration: IllustrationPlan,
    titre: "Plan de plaidoirie chronométré",
    description: "Accroche, points minutés, conclusion – un plan prêt à l'oral, calé sur le temps de parole imparti.",
  },
  {
    Illustration: IllustrationSimulateur,
    titre: "Simulateur d'objections",
    description: "Anticipez les questions pièges du magistrat ou de la partie adverse, avec une piste de réponse pour chacune.",
  },
  {
    Illustration: IllustrationChronologie,
    titre: "Chronologie automatique",
    description: "Reconstitue la timeline d'une affaire à partir des pièces du dossier, période couverte et éléments manquants inclus.",
  },
  {
    Illustration: IllustrationVerification,
    titre: "Vérification procédurale",
    description: "Échéances identifiées avec leur statut, actes de procédure potentiellement manquants, points d'attention.",
  },
];

const ETAPES = [
  {
    numero: "01",
    titre: "Créez un dossier – ou essayez la démo",
    description: "Un dossier fictif de droit du travail, déjà rempli, est prêt à explorer sans inscription ni configuration.",
  },
  {
    numero: "02",
    titre: "Collez vos pièces ou décrivez la situation",
    description: "Conclusions adverses, notes d'audience, question libre : le format d'entrée s'adapte à ce que vous avez sous la main.",
  },
  {
    numero: "03",
    titre: "Obtenez une analyse structurée et vérifiable",
    description: "Chaque réponse signale elle-même ses propres limites – jamais une affirmation présentée comme acquise sans base solide.",
  },
];

export default function LandingPage() {
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
            Fonctionnalités
          </a>
          <a href="#comment-ca-marche" className="transition-colors hover:text-ivory">
            Comment ça marche
          </a>
          <a href="#garde-fou" className="transition-colors hover:text-ivory">
            Vérification multi-agents
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <a
            href={URL_GITHUB}
            target="_blank"
            rel="noreferrer"
            className="hidden text-warmgray transition-colors hover:text-ivory sm:inline-flex"
            aria-label="Code source sur GitHub"
            title="GitHub"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
              <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.09 3.29 9.4 7.86 10.93.58.1.79-.25.79-.56 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.56-.29-5.26-1.28-5.26-5.69 0-1.26.45-2.29 1.18-3.09-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.05 11.05 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.24 2.76.12 3.05.74.8 1.18 1.83 1.18 3.09 0 4.42-2.71 5.4-5.28 5.68.42.36.78 1.08.78 2.17 0 1.56-.01 2.82-.01 3.2 0 .31.2.67.8.56A10.52 10.52 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
            </svg>
          </a>
          <Button variant="primary" onClick={essayerLaDemo}>
            Essayer la démo →
          </Button>
        </div>
      </header>

      {/* --- Hero ------------------------------------------------------ */}
      <section className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-14 px-6 pb-24 pt-8 lg:grid-cols-[1.05fr_1fr] lg:pb-32">
        <div className="glow -left-24 top-0 h-72 w-72 bg-gold-600/20" aria-hidden="true" />
        <div className="glow -right-24 top-40 h-80 w-80 bg-amethyst-600/25" aria-hidden="true" />

        <div className="relative z-10 space-y-6">
          <p className="kicker">Assistant IA de préparation de plaidoirie — France &amp; espace OHADA</p>
          <h1 className="font-display text-4xl font-bold leading-[1.1] text-gold-500 sm:text-5xl">
            Préparez vos dossiers,
            <br />
            pas vos angoisses de dernière minute.
          </h1>
          <p className="max-w-prose text-base leading-relaxed text-warmgray sm:text-lg">
            Plaid'IA analyse des conclusions adverses, chronomètre un plan de plaidoirie, simule les objections du
            magistrat et vérifie la procédure, avec, sur les analyses les plus sensibles, plusieurs contrôles
            indépendants qui vérifient chaque réponse avant qu'elle ne s'affiche.
          </p>
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Button variant="primary" onClick={essayerLaDemo}>
              Essayer la démo →
            </Button>
            <a href={URL_GITHUB} target="_blank" rel="noreferrer" className="btn-secondary">
              Voir le code sur GitHub
            </a>
          </div>
          {demoMode && (
            <p className="text-xs text-muted">
              🎭 Cette instance publique tourne en mode démo — la démo utilise un dossier fictif et des réponses
              préenregistrées, indépendamment de toute clé API.
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
              <span className="ml-2 text-xs text-warmgray">Analyser des conclusions adverses</span>
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
          <p className="kicker mx-auto">Ce que fait l'outil</p>
          <h2 className="mt-2 font-serif text-h1 font-semibold text-gold-500">Six espaces de travail, un même principe : vérifier avant d'affirmer</h2>
        </div>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FONCTIONNALITES.map((f) => (
            <div key={f.titre} className="card group overflow-hidden !p-0">
              <div className="relative aspect-[8/5] overflow-hidden border-b border-gold-600/15 bg-gradient-to-br from-surface-2 to-surface">
                <f.Illustration className="absolute inset-0 h-full w-full p-7 text-amethyst-600/70 transition-transform duration-300 ease-out group-hover:scale-[1.04]" />
              </div>
              <div className="space-y-3 p-6">
                <h3 className="font-serif text-h3 font-semibold text-ivory">{f.titre}</h3>
                <p className="text-sm leading-relaxed text-warmgray">{f.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* --- Comment ça marche ------------------------------------------- */}
      <section id="comment-ca-marche" className="relative mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="kicker mx-auto">Prise en main</p>
          <h2 className="mt-2 font-serif text-h1 font-semibold text-gold-500">Comment ça marche</h2>
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
        <img src={justitiaBanniere} alt="Statue de la Justice tenant une balance, en contre-plongée" />
        <div className="banner-scrim" aria-hidden="true" />
        <div className="banner-wash" aria-hidden="true" />
        <div className="banner-edgefade" aria-hidden="true" />
        <div className="relative z-10 mx-auto w-full max-w-6xl px-6 sm:px-10">
          <p className="kicker">Ce que l'outil ne fera jamais</p>
          <h2 className="mt-3 max-w-xl font-display text-3xl font-bold leading-tight text-ivory sm:text-4xl">
            Peser chaque argument,
            <br />
            <span className="text-gold-500">jamais trancher à votre place.</span>
          </h2>
        </div>
      </section>

      {/* --- Garde-fou anti-hallucination : architecture multi-agents ----- */}
      <section id="garde-fou" className="relative mx-auto max-w-5xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="kicker mx-auto">Plusieurs garde-fous, un même objectif</p>
          <h2 className="mt-2 font-serif text-h1 font-semibold text-gold-500">Vérifier avant d'affirmer</h2>
          <p className="mx-auto mt-4 max-w-prose text-sm leading-relaxed text-warmgray sm:text-base">
            Sur les analyses les plus sensibles, l'agent qui rédige n'est jamais le seul juge de sa propre réponse.
            Avant qu'elle n'atteigne l'écran, cinq contrôles indépendants l'examinent chacun sous un angle différent —
            et chaque affirmation reste marquée <mark className="marker-verify">À VÉRIFIER</mark> tant qu'aucun
            d'eux n'a pu la confirmer.
          </p>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {[
            {
              icone: "🛡",
              titre: "Sécurité",
              texte: "Contrôle la demande — hors-sujet, ambiguë ou manipulatrice — avant qu'elle n'atteigne un agent d'analyse.",
              photo: gardeFouSecurite,
              photoAlt: "Armure métallique ancienne, faiblement éclairée dans la pénombre",
            },
            {
              icone: "🎯",
              titre: "Intention",
              texte: "Comprend ce qui est réellement demandé, et détermine si la question appelle une vérification approfondie.",
              photo: gardeFouIntention,
              photoAlt: "Fléchette plantée au centre d'une cible, sur fond sombre",
            },
            {
              icone: "📚",
              titre: "Vérification juridique",
              texte: "Confronte chaque référence citée aux sources réellement disponibles — jamais une confirmation de complaisance.",
              photo: gardeFouVerification,
              photoAlt: "Statuette de la Justice, un marteau de juge et un livre de droit ouvert",
            },
            {
              icone: "⚖",
              titre: "Critique",
              texte: "Joue le contradicteur : cherche activement les faiblesses du raisonnement, comme le ferait la partie adverse.",
              photo: gardeFouCritique,
              photoAlt: "Deux pièces d'échecs, roi et reine, face à face sur un échiquier",
            },
            {
              icone: "✓",
              titre: "Validation",
              texte: "Consolide les deux contrôles précédents en un statut clair — sans jamais inventer une source pour combler un doute.",
              photo: null,
              photoAlt: "",
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
          Plusieurs contrôles indépendants ne rendent pas une réponse automatiquement correcte — ils aident à repérer
          plus tôt les erreurs, les contradictions et les points qui restent à vérifier. Plaid'IA distingue toujours
          ce qui est vérifié, ce qui est probable, et ce qui reste incertain.
        </p>
      </section>

      {/* --- Footer ------------------------------------------------------- */}
      <footer className="relative border-t border-gold-600/15 bg-surface/60">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="grid grid-cols-1 gap-10 sm:grid-cols-3">
            <div className="space-y-3">
              <Logo iconClassName="h-6 w-6 text-gold-500" wordmarkClassName="font-display text-lg font-bold text-gold-500" />
              <p className="max-w-xs text-sm text-warmgray">
                Assistant de préparation de plaidoirie pour avocats et greffiers, France et espace OHADA.
              </p>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-micro font-medium uppercase tracking-wide text-warmgray">Le produit</p>
              <a href="#fonctionnalites" className="block text-ivory hover:text-gold-500">
                Fonctionnalités
              </a>
              <a href="#comment-ca-marche" className="block text-ivory hover:text-gold-500">
                Comment ça marche
              </a>
              <Link to="/app/chemise/dossiers" className="block text-ivory hover:text-gold-500">
                Essayer la démo
              </Link>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-micro font-medium uppercase tracking-wide text-warmgray">Contact</p>
              <a href={URL_GITHUB} target="_blank" rel="noreferrer" className="block text-ivory hover:text-gold-500">
                GitHub
              </a>
              <a href={URL_LINKEDIN} target="_blank" rel="noreferrer" className="block text-ivory hover:text-gold-500">
                LinkedIn
              </a>
              <p className="pt-1 text-xs text-muted">Projet portfolio, Abdoulaye Sadio, NLP / TAL</p>
            </div>
          </div>

          <div className="mt-10 border-t border-gold-600/10 pt-6 text-center text-xs text-muted">
            Plaid'IA est un outil d'aide à la préparation — il ne remplace pas l'analyse d'un avocat. Aucune donnée
            n'est conservée en mode démo.
          </div>
        </div>
      </footer>
    </div>
  );
}
