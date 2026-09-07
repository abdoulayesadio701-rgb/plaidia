/**
 * ResumerDossierPage — /arsenal/resumer. Ne nécessite que le dossier actif
 * (aucune saisie), mais reste déclenché par un clic explicite plutôt
 * qu'auto-lancé à la navigation — même règle que tout l'Arsenal, un appel
 * IA a un coût réel, jamais silencieux.
 */

import { analyse as analyseApi } from "@/api";
import { useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

export default function ResumerDossierPage() {
  const dossierActif = useDossierActif();
  const { data, loading, error, executer, definirDonnees } = useLazyAction(() => analyseApi.resumerDossier(dossierActif!.id));

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour le résumer." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="kicker">L'Arsenal</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Résumer ce dossier</h1>
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
          titre="Prêt à résumer"
          description="Synthétise les faits, parties et arguments déjà accumulés dans ce dossier."
          action={
            <Button variant="primary" onClick={() => void executer()}>
              Résumer ce dossier
            </Button>
          }
        />
      )}

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="card p-6">
            <p className="kicker">Résumé</p>
            <RichOutput texte={data.resume_court} className="mt-3" />
          </div>

          {data.points_cles.length > 0 && (
            <div className="card p-6">
              <p className="mb-3 text-micro font-medium uppercase tracking-wide text-gold-500">Points clés</p>
              <ul className="space-y-2">
                {data.points_cles.map((p, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-gold-500">•</span>
                    <RichOutput texte={p} prose={false} className="flex-1 text-sm" />
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.elements_manquants.length > 0 && (
            <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-5">
              <p className="mb-2 text-sm font-semibold text-gold-500">Éléments manquants</p>
              <ul className="space-y-1.5">
                {data.elements_manquants.map((e, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-gold-500">•</span>
                    <RichOutput texte={e} prose={false} className="flex-1 text-sm" />
                  </li>
                ))}
              </ul>
            </div>
          )}

          <ChatContextuelPanel
            feature="resume"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            placeholder="Ex. « Insiste davantage sur le risque de prescription », « fais plus court »…"
          />
        </div>
      )}
    </div>
  );
}
