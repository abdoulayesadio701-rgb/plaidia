/**
 * HistoriqueDossierPage — /chemise/historique. Fiche du dossier actif
 * (faits, parties, domaine) + historique de ses analyses de conclusions en
 * accordéon (une analyse par ligne enregistrée via /arsenal/analyser, voir
 * GET /api/dossiers/{id}/analyses).
 */

import { dossiers as dossiersApi } from "@/api";
import { useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import ArgumentCard from "@/components/ArgumentCard";
import Accordion from "@/components/Accordion";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

function formaterDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export default function HistoriqueDossierPage() {
  const dossierActif = useDossierActif();

  const { data: analyses, loading, error, reload } = useAsync(
    () => dossiersApi.historiqueAnalyses(dossierActif!.id),
    [dossierActif?.id],
    dossierActif !== null
  );

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour consulter sa fiche et son historique." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">La Chemise</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{dossierActif.nom}</h1>
      </div>

      <div className="card space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-3">
          {dossierActif.domaine && <span className="badge border-gold-600/30 bg-surface-2 text-gold-500">{dossierActif.domaine}</span>}
          <span className="badge border-gold-600/30 bg-surface-2 text-warmgray">{dossierActif.statut}</span>
          {dossierActif.numero_dossier && <span className="text-xs text-muted">Réf. {dossierActif.numero_dossier}</span>}
        </div>

        <div>
          <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">Parties</p>
          <p className="text-sm text-ivory">{dossierActif.parties?.trim() || <span className="text-muted">Non renseignées.</span>}</p>
        </div>

        <div>
          <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">Faits</p>
          {dossierActif.faits?.trim() ? (
            <div className="max-h-72 overflow-y-auto whitespace-pre-wrap rounded-md bg-surface-2 p-4 text-sm leading-relaxed text-ivory">
              {dossierActif.faits}
            </div>
          ) : (
            <p className="text-sm text-muted">
              Aucun fait enregistré — utilisez « Préparer ce dossier » pour en importer.
            </p>
          )}
        </div>
      </div>

      <div>
        <h2 className="mb-3 font-serif text-h3 font-semibold text-gold-500">Historique des analyses</h2>

        {loading && <SkeletonList count={2} />}

        {!loading && error && <ErrorState message={error} onRetry={reload} />}

        {!loading && !error && analyses && analyses.length === 0 && (
          <EmptyState
            titre="Aucune analyse enregistrée"
            description="Chaque analyse lancée depuis « Analyser des conclusions adverses » est automatiquement archivée ici."
          />
        )}

        {!loading && !error && analyses && analyses.length > 0 && (
          <Accordion
            ouvertParDefaut={analyses[0].id}
            items={analyses.map((a) => ({
              id: a.id,
              header: (
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-sm font-medium text-ivory">{formaterDate(a.date)}</span>
                  <span className="text-xs text-warmgray">
                    {a.arguments.length} argument{a.arguments.length > 1 ? "s" : ""}
                  </span>
                  {a.points_attention.length > 0 && (
                    <span className="badge border-risk-high/30 bg-risk-high/10 text-risk-high">{a.points_attention.length} point(s) d'attention</span>
                  )}
                </div>
              ),
              content: (
                <div className="space-y-4">
                  {a.arguments.map((arg, i) => (
                    <ArgumentCard key={i} argument={arg} index={i} />
                  ))}
                  {a.points_attention.length > 0 && (
                    <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-4">
                      <p className="mb-2 text-sm font-semibold text-risk-high">⚠ Points d'attention</p>
                      <ul className="space-y-1 text-sm text-ivory">
                        {a.points_attention.map((p, i) => (
                          <li key={i} className="flex gap-2">
                            <span className="text-risk-high">•</span>
                            <span>{p}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ),
            }))}
          />
        )}
      </div>
    </div>
  );
}
