/**
 * ParametresPage — /app/parametres. Regroupe les réglages jusque-là
 * éparpillés dans l'app : la juridiction active (déplacée depuis "Gérer le
 * corpus multi-source", voir GererCorpusPage.tsx) et la clé API personnelle
 * (déplacée depuis le bandeau du mode démo, toujours accessible aussi depuis
 * là où elle est utile dans l'instant -- voir ClePersonnelleModal.tsx, qui
 * réutilise le même formulaire). Accessible en permanence depuis la TopBar,
 * pas seulement depuis un espace de travail précis (avocat ou greffier) --
 * voir router.tsx, ajouté hors de la liste pilotée par navigation.ts.
 */

import { useAppStore } from "@/store/useAppStore";
import ClePersonnelleForm from "@/components/ClePersonnelleForm";

const URL_GITHUB = "https://github.com/abdoulayesadio701-rgb/plaidia";

export default function ParametresPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <p className="kicker">Réglages</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Paramètres</h1>
      </div>

      <JuridictionSection />
      <ClePersonnelleSection />
      <AProposSection />
    </div>
  );
}

function JuridictionSection() {
  const juridictionActive = useAppStore((s) => s.juridictionActive);
  const definirJuridictionActive = useAppStore((s) => s.definirJuridictionActive);
  const sourcesJuridictions = useAppStore((s) => s.sourcesJuridictions);

  return (
    <section className="card space-y-3 p-6">
      <h2 className="font-serif text-h3 font-semibold text-gold-500">Juridiction active</h2>
      <p className="text-sm text-warmgray">
        Détermine le contexte utilisé par l'agent pour « Consulter la jurisprudence » et le Chat. Seules les sources du corpus déjà
        validées apparaissent ici, en plus de Légifrance — gérez-les depuis Le Grimoire → Gérer le corpus multi-source.
      </p>
      <select
        className="input max-w-sm"
        value={juridictionActive}
        onChange={(e) => void definirJuridictionActive(e.target.value)}
        aria-label="Juridiction active"
      >
        {sourcesJuridictions.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
    </section>
  );
}

function ClePersonnelleSection() {
  return (
    <section className="card space-y-3 p-6">
      <h2 className="font-serif text-h3 font-semibold text-gold-500">Clé API Anthropic personnelle</h2>
      <ClePersonnelleForm />
    </section>
  );
}

function AProposSection() {
  return (
    <section className="card space-y-3 p-6">
      <h2 className="font-serif text-h3 font-semibold text-gold-500">À propos</h2>
      <p className="text-sm leading-relaxed text-warmgray">
        Plaid'IA est un outil d'aide à la préparation pour avocats et greffiers, France et espace OHADA. Chaque réponse signale
        elle-même ce qui reste à vérifier plutôt que de présenter une déduction comme un fait établi — voir la balise{" "}
        <mark className="marker-verify">À VÉRIFIER : ...</mark> dans les réponses de l'agent, à distinguer d'une référence
        citée avec confiance comme <span className="marker-citation">art. 1240 du Code civil</span>.
      </p>
      <a href={URL_GITHUB} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-sm text-amethyst-400 hover:underline">
        Code source sur GitHub ↗
      </a>
    </section>
  );
}
