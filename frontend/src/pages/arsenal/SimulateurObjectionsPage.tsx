/**
 * SimulateurObjectionsPage — /arsenal/simulateur. Mode "entraînement" :
 * masque la piste de réponse jusqu'au clic, pour répéter à l'oral sans se
 * la faire souffler — désactiver le mode l'affiche tout de suite (relecture).
 */

import { useState } from "react";
import { analyse as analyseApi } from "@/api";
import { useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import LabeledField from "@/components/LabeledField";
import { SkeletonList } from "@/components/Skeleton";

export default function SimulateurObjectionsPage() {
  const dossierActif = useDossierActif();
  const [modeEntrainement, setModeEntrainement] = useState(false);
  const [revelees, setRevelees] = useState<Set<number>>(new Set());

  const { data, loading, error, executer } = useLazyAction(() => analyseApi.simulerObjections(dossierActif!.id));

  const basculerEntrainement = () => {
    setModeEntrainement((v) => !v);
    setRevelees(new Set()); // repart de zéro à chaque bascule -- l'entraînement recommence masqué
  };

  const reveler = (i: number) => setRevelees((prev) => new Set(prev).add(i));

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour simuler ses objections probables." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="kicker">L'Arsenal</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Simuler les objections probables</h1>
          <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
        </div>
        {data && (
          <Button variant="ghost" loading={loading} onClick={() => void executer()}>
            🔄 Relancer
          </Button>
        )}
      </div>

      {!data && !loading && !error && (
        <EmptyState
          titre="Prêt à simuler"
          description="Anticipe les questions et objections les plus probables du juge ou de la partie adverse."
          action={
            <Button variant="primary" onClick={() => void executer()}>
              Simuler les objections
            </Button>
          }
        />
      )}

      {loading && <SkeletonList count={3} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <label className="flex w-fit cursor-pointer items-center gap-2.5 rounded-md border border-gold-600/20 bg-surface px-4 py-2.5 text-sm text-warmgray">
            <button
              type="button"
              role="switch"
              aria-checked={modeEntrainement}
              onClick={basculerEntrainement}
              className={`relative h-5 w-9 shrink-0 rounded-pill transition-colors ${modeEntrainement ? "bg-amethyst-400" : "bg-surface-3"}`}
            >
              <span
                className={`absolute top-0.5 h-4 w-4 rounded-pill bg-ivory transition-transform ${
                  modeEntrainement ? "translate-x-[18px]" : "translate-x-0.5"
                }`}
              />
            </button>
            Mode entraînement — masquer les pistes de réponse
          </label>

          {data.objections.length === 0 ? (
            <EmptyState titre="Aucune objection identifiée" description="Le contexte actuel du dossier ne permet pas d'anticiper d'objection probable." />
          ) : (
            <div className="space-y-4">
              {data.objections.map((obj, i) => {
                const masquee = modeEntrainement && !revelees.has(i);
                return (
                  <div key={i} className="card space-y-3 p-6">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <p className="font-serif text-h4 font-semibold text-ivory">
                        <span className="mr-2 text-warmgray">{i + 1}.</span>
                        {obj.question}
                      </p>
                      <span className="shrink-0 rounded-pill border border-amethyst-400/40 bg-amethyst-400/10 px-2.5 py-0.5 text-micro font-medium text-amethyst-400">
                        {obj.origine}
                      </span>
                    </div>

                    <LabeledField label="Piège" texte={obj.piege} />

                    {masquee ? (
                      <Button variant="secondary" onClick={() => reveler(i)}>
                        👁 Révéler la piste de réponse
                      </Button>
                    ) : (
                      <LabeledField label="Piste de réponse" texte={obj.piste_reponse} />
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {data.point_le_plus_faible && (
            <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
              <p className="mb-2 text-sm font-semibold text-risk-high">⚠ Point le plus faible du dossier</p>
              <RichOutput texte={data.point_le_plus_faible} prose={false} className="text-sm" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
