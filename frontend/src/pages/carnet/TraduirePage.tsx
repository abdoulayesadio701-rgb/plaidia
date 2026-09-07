/**
 * TraduirePage — /carnet/traduire. Ne nécessite pas de dossier actif (voir
 * navigation.ts, requiresDossier: false) — traduction juridique français ↔
 * anglais d'un texte collé, indépendante d'un dossier précis. Utilise Claude
 * directement (voir analyse.py::traduire_texte) plutôt qu'un moteur de
 * traduction générique, pour préserver la terminologie juridique précise.
 */

import { useState } from "react";
import { analyse as analyseApi } from "@/api";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonBlock } from "@/components/Skeleton";

const LABEL_LANGUE: Record<string, string> = { fr: "Français", en: "English" };

export default function TraduirePage() {
  const [texte, setTexte] = useState("");
  const { data, loading, error, executer } = useLazyAction((t: string) => analyseApi.traduireTexte(t));

  const copier = async () => {
    if (!data?.texte_traduit) return;
    try {
      await navigator.clipboard.writeText(data.texte_traduit);
    } catch {
      // Silencieux : le texte reste sélectionnable/copiable à la main dans la carte ci-dessous.
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">Le Carnet</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Traduire un texte</h1>
        <p className="mt-2 text-sm text-warmgray">
          Français → anglais ou anglais → français, détecté automatiquement. Le registre juridique et le marqueur "À VÉRIFIER" sont
          préservés — utile pour partager une note ou une analyse avec un confrère ou une partie anglophone.
        </p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          className="input min-h-[200px] resize-y"
          placeholder="Collez ici le texte à traduire, en français ou en anglais…"
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          disabled={loading}
        />
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} disabled={!texte.trim()} onClick={() => void executer(texte)}>
            Traduire
          </Button>
        </div>
      </div>

      {loading && (
        <div className="card space-y-2.5 p-6">
          <SkeletonBlock className="h-4 w-1/3" />
          <SkeletonBlock className="h-4 w-full" />
          <SkeletonBlock className="h-4 w-5/6" />
          <SkeletonBlock className="h-4 w-2/3" />
        </div>
      )}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer(texte)} />}

      {!loading && !error && data && (
        <div className="card space-y-4 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">
              {LABEL_LANGUE[data.langue_detectee] ?? data.langue_detectee} détecté → traduit en {LABEL_LANGUE[data.langue_cible] ?? data.langue_cible}
            </p>
            <button onClick={() => void copier()} className="text-xs text-amethyst-400 hover:underline">
              Copier la traduction
            </button>
          </div>
          <RichOutput texte={data.texte_traduit} />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à traduire" description="Collez un texte ci-dessus — la langue source est détectée automatiquement." />
      )}
    </div>
  );
}
