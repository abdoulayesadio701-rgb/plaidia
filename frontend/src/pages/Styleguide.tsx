/**
 * Styleguide — démonstration vivante du design system Plaid'IA.
 * Chaque section renvoie à la règle correspondante dans DESIGN.md.
 * Volontairement construite avec du contenu réaliste (texte d'analyse,
 * référence de jurisprudence) plutôt que du lorem ipsum.
 */
import { useState } from "react";
import Logo from "../components/Logo";
import GothicMotif from "../components/GothicMotif";

const PALETTE: { title: string; swatches: { name: string; className: string; hex: string }[] }[] = [
  {
    title: "Fond — noir violacé",
    swatches: [
      { name: "void", className: "bg-void border border-gold-600/20", hex: "#0B0A0F" },
      { name: "surface", className: "bg-surface border border-gold-600/20", hex: "#14111C" },
      { name: "surface-2", className: "bg-surface-2 border border-gold-600/20", hex: "#1C1826" },
      { name: "surface-3", className: "bg-surface-3 border border-gold-600/20", hex: "#241E33" },
    ],
  },
  {
    title: "Or ancien — couleur principale",
    swatches: [
      { name: "gold-300", className: "bg-gold-300", hex: "#F0DDA0" },
      { name: "gold-400", className: "bg-gold-400", hex: "#E6C76A" },
      { name: "gold-500", className: "bg-gold-500", hex: "#C9A227" },
      { name: "gold-600", className: "bg-gold-600", hex: "#B8860B" },
      { name: "gold-700", className: "bg-gold-700", hex: "#8A6508" },
    ],
  },
  {
    title: "Améthyste — accent d'état",
    swatches: [
      { name: "amethyst-300", className: "bg-amethyst-300", hex: "#C4B5FD" },
      { name: "amethyst-400", className: "bg-amethyst-400", hex: "#8B5CF6" },
      { name: "amethyst-600", className: "bg-amethyst-600", hex: "#6E3FA3" },
      { name: "amethyst-700", className: "bg-amethyst-700", hex: "#55317F" },
    ],
  },
  {
    title: "Risque",
    swatches: [
      { name: "risk-high", className: "bg-risk-high", hex: "#B3261E" },
      { name: "risk-medium", className: "bg-risk-medium", hex: "#C9A227" },
      { name: "risk-low", className: "bg-risk-low", hex: "#4C6B3F" },
    ],
  },
];

const TABS = [
  { id: "arsenal", label: "L'Arsenal" },
  { id: "chemise", label: "La Chemise" },
  { id: "grimoire", label: "Le Grimoire" },
  { id: "carnet", label: "Le Carnet" },
];

export default function Styleguide() {
  const [activeTab, setActiveTab] = useState(TABS[0].id);

  return (
    <div className="min-h-screen bg-void text-ivory">
      {/* ---------- Hero / identité ---------- */}
      <header className="relative overflow-hidden border-b border-gold-600/20 px-8 py-16 sm:px-16">
        <GothicMotif className="pointer-events-none absolute right-8 top-0 h-full w-auto text-gold-500 opacity-[0.06]" />
        <div className="relative max-w-prose">
          <Logo className="mb-6" />
          <h1 className="font-serif text-h1 font-semibold text-gold-500">Design system</h1>
          <p className="mt-3 text-warmgray">
            Tokens, composants et règles d'usage de Plaid'IA — un cabinet d'avocat ancien
            revisité, sérieux avant tout. Référence vivante pour DESIGN.md.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-16 px-8 py-16 sm:px-16">
        {/* ---------- Palette ---------- */}
        <section aria-labelledby="palette-title">
          <h2 id="palette-title" className="font-serif text-h2 font-semibold text-gold-500">
            Couleur
          </h2>
          <div className="mt-8 space-y-8">
            {PALETTE.map((group) => (
              <div key={group.title}>
                <h3 className="font-serif text-h4 text-ivory">{group.title}</h3>
                <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
                  {group.swatches.map((s) => (
                    <div key={s.name} className="overflow-hidden rounded-md border border-gold-600/20">
                      <div className={`h-16 ${s.className}`} />
                      <div className="bg-surface px-3 py-2">
                        <p className="font-mono text-xs text-ivory">{s.name}</p>
                        <p className="font-mono text-xs text-warmgray">{s.hex}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Marqueur À VÉRIFIER — traité à part, ce n'est pas un token de palette générique */}
            <div>
              <h3 className="font-serif text-h4 text-ivory">Marqueur "À VÉRIFIER"</h3>
              <div className="mt-3 max-w-xs overflow-hidden rounded-md border border-gold-600/20">
                <div className="flex h-16 items-center justify-center bg-verify-bg">
                  <span className="font-bold text-verify-text">À VÉRIFIER</span>
                </div>
                <div className="bg-surface px-3 py-2">
                  <p className="font-mono text-xs text-ivory">verify-bg / verify-text</p>
                  <p className="font-mono text-xs text-warmgray">#FFE9B0 / #7A4A00</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ---------- Typographie ---------- */}
        <section aria-labelledby="type-title">
          <h2 id="type-title" className="font-serif text-h2 font-semibold text-gold-500">
            Typographie
          </h2>
          <div className="mt-8 space-y-5 rounded-md border border-gold-600/20 bg-surface p-6">
            <p className="font-display text-display font-bold text-gold-500">Plaid'IA</p>
            <p className="font-serif text-h1 font-semibold">Analyse des conclusions adverses</p>
            <p className="font-serif text-h2 font-semibold">Vérification procédurale</p>
            <p className="font-serif text-h3">Article 1130 du Code civil</p>
            <p className="font-serif text-h4 text-warmgray">Domaine : bail commercial</p>
            <p className="max-w-prose text-body">
              Le défendeur soutient que le contrat signé le 12 mars 2020 est nul pour vice du
              consentement, la partie demanderesse ayant été induite en erreur sur les qualités
              substantielles du bien vendu.
            </p>
            <p className="text-small text-warmgray">Généré le 04/09/2026 à 14:32 — dossier Martin bail commercial</p>
            <p className="font-mono text-small text-ivory">Cass. civ. 1re, 12 mars 2020, n° 18-19.827</p>
          </div>
        </section>

        {/* ---------- Boutons ---------- */}
        <section aria-labelledby="btn-title">
          <h2 id="btn-title" className="font-serif text-h2 font-semibold text-gold-500">
            Boutons
          </h2>
          <div className="mt-8 flex flex-wrap items-center gap-4 rounded-md border border-gold-600/20 bg-surface p-6">
            <button className="btn-primary">Analyser les conclusions</button>
            <button className="btn-secondary">Exporter en Word</button>
            <button className="btn-ghost">Annuler</button>
            <button className="btn-primary" disabled>
              Analyse en cours…
            </button>
          </div>
        </section>

        {/* ---------- Cartes ---------- */}
        <section aria-labelledby="card-title">
          <h2 id="card-title" className="font-serif text-h2 font-semibold text-gold-500">
            Cartes
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            <div className="card">
              <h3 className="font-serif text-h3">Dossier Martin</h3>
              <p className="mt-2 text-small text-warmgray">Bail commercial — 6 mois d'impayés</p>
              <p className="mt-4 text-body">
                SCI Beaulieu (bailleur) c. M. Martin (preneur). Le bailleur invoque la clause
                résolutoire pour non-paiement des loyers commerciaux.
              </p>
            </div>
            <div className="card-interactive">
              <h3 className="font-serif text-h3">Dossier Diallo</h3>
              <p className="mt-2 text-small text-warmgray">Divorce pour faute — survolez-moi</p>
              <p className="mt-4 text-body">
                Mme Diallo demande le divorce pour faute après 12 ans de mariage, invoquant des
                infidélités répétées et un abandon financier du foyer.
              </p>
            </div>
          </div>
        </section>

        {/* ---------- Badges de risque ---------- */}
        <section aria-labelledby="badge-title">
          <h2 id="badge-title" className="font-serif text-h2 font-semibold text-gold-500">
            Badges de risque
          </h2>
          <div className="mt-8 flex flex-wrap gap-3 rounded-md border border-gold-600/20 bg-surface p-6">
            <span className="badge-risk-high">Élevé</span>
            <span className="badge-risk-medium">Moyen</span>
            <span className="badge-risk-low">Faible</span>
          </div>
        </section>

        {/* ---------- Marqueur À VÉRIFIER en contexte ---------- */}
        <section aria-labelledby="verify-title">
          <h2 id="verify-title" className="font-serif text-h2 font-semibold text-gold-500">
            Marqueur "À VÉRIFIER" en contexte
          </h2>
          <div className="mt-8 max-w-prose rounded-md border border-gold-600/20 bg-surface p-6">
            <p className="text-body">
              L'article 1132 du Code civil précise que l'erreur de droit ou de fait est une cause
              de nullité lorsqu'elle porte sur les qualités essentielles de la prestation due.{" "}
              <mark className="marker-verify">À VÉRIFIER : l'excusabilité de l'erreur alléguée n'est pas établie par les pièces citées</mark>{" "}
              — il conviendra de solliciter les pièces précontractuelles avant l'audience.
            </p>
          </div>
        </section>

        {/* ---------- Input ---------- */}
        <section aria-labelledby="input-title">
          <h2 id="input-title" className="font-serif text-h2 font-semibold text-gold-500">
            Champs de saisie
          </h2>
          <div className="mt-8 max-w-sm space-y-4 rounded-md border border-gold-600/20 bg-surface p-6">
            <div>
              <label htmlFor="sg-dossier" className="mb-1.5 block text-small text-warmgray">
                Nom du dossier
              </label>
              <input id="sg-dossier" className="input" defaultValue="Martin bail commercial" />
            </div>
            <div>
              <label htmlFor="sg-focus" className="mb-1.5 block text-small text-warmgray">
                Rechercher une décision (focus clavier — Tab jusqu'ici)
              </label>
              <input id="sg-focus" className="input" placeholder="rupture contrat travail…" />
            </div>
          </div>
        </section>

        {/* ---------- Tabs ---------- */}
        <section aria-labelledby="tabs-title">
          <h2 id="tabs-title" className="font-serif text-h2 font-semibold text-gold-500">
            Onglets
          </h2>
          <div className="mt-8 rounded-md border border-gold-600/20 bg-surface p-6">
            <div className="tabs-list" role="tablist">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  className={activeTab === tab.id ? "tab-active" : "tab"}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <p className="mt-6 text-body text-warmgray">
              Section active : <span className="text-ivory">{TABS.find((t) => t.id === activeTab)?.label}</span>
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
