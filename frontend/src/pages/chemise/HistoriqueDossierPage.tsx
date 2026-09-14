/**
 * HistoriqueDossierPage — /chemise/historique. Fiche du dossier actif
 * (faits, parties, domaine) + historique de ses analyses de conclusions en
 * accordéon (une analyse par ligne enregistrée via /arsenal/analyser, voir
 * GET /api/dossiers/{id}/analyses).
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, dossiers as dossiersApi } from "@/api";
import type { StatutDocument } from "@/api";
import { chat as chatApi } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { Link } from "react-router-dom";
import ArgumentCard from "@/components/ArgumentCard";
import Accordion from "@/components/Accordion";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";
import StatutDocumentMenu, { StatutDocumentBadge } from "@/components/StatutDocument";

function formaterDate(iso: string, langue: string): string {
  try {
    const locale = langue === "en" ? "en-GB" : "fr-FR";
    return new Date(iso).toLocaleDateString(locale, { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export default function HistoriqueDossierPage() {
  const { t, i18n } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [statuts, setStatuts] = useState<Record<number, StatutDocument>>({});
  const [statutEnCours, setStatutEnCours] = useState<number | null>(null);

  const { data: analyses, loading, error, reload } = useAsync(
    () => dossiersApi.historiqueAnalyses(dossierActif!.id),
    [dossierActif?.id],
    dossierActif !== null
  );

  const {
    data: conversations,
    loading: conversationsLoading,
    error: conversationsError,
    reload: reloadConversations,
  } = useAsync(
    () => chatApi.listerConversationsDossier(dossierActif!.id),
    [dossierActif?.id],
    dossierActif !== null
  );

  const {
    data: documentsGeneres,
    loading: documentsLoading,
    error: documentsError,
    reload: reloadDocuments,
  } = useAsync(
    () => dossiersApi.listerDocumentsGeneres(dossierActif!.id),
    [dossierActif?.id],
    dossierActif !== null
  );

  useEffect(() => {
    if (analyses) setStatuts(Object.fromEntries(analyses.map((analyse) => [analyse.id, analyse.statut])));
  }, [analyses]);

  const changerStatut = async (analyseId: number, statut: StatutDocument) => {
    setStatutEnCours(analyseId);
    try {
      await analyseApi.changerStatutConclusion(analyseId, statut);
      setStatuts((precedents) => ({ ...precedents, [analyseId]: statut }));
      pousserToast("success", t("statutDocument.changePousse", { statut: t(`statutDocument.${statut}`, statut) }));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurChangementStatut"));
    } finally {
      setStatutEnCours(null);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("historiqueDossier.emptyTitre")} description={t("historiqueDossier.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.chemise")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{dossierActif.nom}</h1>
        <Link to={`/app/chat?dossier_id=${dossierActif.id}`} className="btn-secondary mt-3 inline-flex">
          {t("historiqueDossier.ouvrirChat")}
        </Link>
      </div>

      <div className="card space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-3">
          {dossierActif.domaine && <span className="badge border-gold-600/30 bg-surface-2 text-gold-500">{dossierActif.domaine}</span>}
          <span className="badge border-gold-600/30 bg-surface-2 text-warmgray">{t(`dossierStatut.${dossierActif.statut}`, dossierActif.statut)}</span>
          {dossierActif.numero_dossier && <span className="text-xs text-muted">{t("dossiersPage.reference")} {dossierActif.numero_dossier}</span>}
          {dossierActif.partie_representee && <span className="badge border-amethyst-400/30 bg-amethyst-400/10 text-amethyst-400">{dossierActif.partie_representee}</span>}
          {dossierActif.stade_procedure && <span className="badge border-gold-600/30 bg-surface-2 text-gold-500">{dossierActif.stade_procedure}</span>}
        </div>

        {dossierActif.objectif && (
          <div>
            <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">{t("modifierDomaine.objectif")}</p>
            <p className="text-sm text-ivory">{dossierActif.objectif}</p>
          </div>
        )}

        <div>
          <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">{t("historiqueDossier.parties")}</p>
          <p className="text-sm text-ivory">{dossierActif.parties?.trim() || <span className="text-muted">{t("historiqueDossier.partiesNonRenseignees")}</span>}</p>
        </div>

        <div>
          <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">{t("historiqueDossier.faits")}</p>
          {dossierActif.faits?.trim() ? (
            <div className="max-h-72 overflow-y-auto whitespace-pre-wrap rounded-md bg-surface-2 p-4 text-sm leading-relaxed text-ivory">
              {dossierActif.faits}
            </div>
          ) : (
            <p className="text-sm text-muted">
              {t("historiqueDossier.aucunFait")}
            </p>
          )}
        </div>
      </div>

      <div>
        <h2 className="mb-3 font-serif text-h3 font-semibold text-gold-500">{t("historiqueDossier.documentsGeneres")}</h2>
        {documentsLoading && <SkeletonList count={2} />}
        {!documentsLoading && documentsError && <ErrorState message={documentsError} onRetry={reloadDocuments} />}
        {!documentsLoading && !documentsError && documentsGeneres && documentsGeneres.length === 0 && (
          <EmptyState titre={t("historiqueDossier.aucunDocumentTitre")} description={t("historiqueDossier.aucunDocumentDescription")} />
        )}
        {!documentsLoading && !documentsError && documentsGeneres && documentsGeneres.length > 0 && (
          <div className="space-y-2">
            {documentsGeneres.map((document) => {
              const chemin = document.feature === "plan" ? "arsenal/plan" : document.feature === "simulateur" ? "arsenal/simulateur" : "grimoire/jurisprudence";
              return (
                <Link
                  key={document.id}
                  to={`/app/${chemin}?document_id=${document.id}`}
                  className="card flex items-center justify-between gap-4 p-4 transition-colors hover:border-gold-500/40"
                >
                  <div className="min-w-0"><p className="truncate text-sm font-medium text-ivory">{document.titre}</p><p className="text-xs text-muted">{document.feature}</p></div>
                  <div className="flex shrink-0 items-center gap-2"><StatutDocumentBadge statut={document.statut} /><span className="text-xs text-muted">{t("historiqueDossier.rouvrir")}</span></div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-3 font-serif text-h3 font-semibold text-gold-500">{t("historiqueDossier.conversations")}</h2>

        {conversationsLoading && <SkeletonList count={2} />}

        {!conversationsLoading && conversationsError && <ErrorState message={conversationsError} onRetry={reloadConversations} />}

        {!conversationsLoading && !conversationsError && conversations && conversations.length === 0 && (
          <EmptyState
            titre={t("historiqueDossier.aucuneConversationTitre")}
            description={t("historiqueDossier.aucuneConversationDescription")}
          />
        )}

        {!conversationsLoading && !conversationsError && conversations && conversations.length > 0 && (
          <div className="space-y-2">
            {conversations.map((conversation) => (
              <Link
                key={conversation.id}
                to={`/app/chat?conversation_id=${conversation.id}`}
                className="card flex items-center justify-between gap-4 p-4 transition-colors hover:border-gold-500/40"
              >
                <span className="min-w-0 truncate text-sm font-medium text-ivory">{conversation.titre}</span>
                <span className="shrink-0 text-xs text-muted">{formaterDate(conversation.date_modification, i18n.language)}</span>
              </Link>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-3 font-serif text-h3 font-semibold text-gold-500">{t("historiqueDossier.historiqueAnalyses")}</h2>

        {loading && <SkeletonList count={2} />}

        {!loading && error && <ErrorState message={error} onRetry={reload} />}

        {!loading && !error && analyses && analyses.length === 0 && (
          <EmptyState
            titre={t("rapportComplet.aucuneAnalyseTitre")}
            description={t("historiqueDossier.aucuneAnalyseDescription")}
          />
        )}

        {!loading && !error && analyses && analyses.length > 0 && (
          <Accordion
            ouvertParDefaut={analyses[0].id}
            items={analyses.map((a) => ({
              id: a.id,
              header: (() => {
                const statut = statuts[a.id] ?? a.statut;
                return (
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-sm font-medium text-ivory">{formaterDate(a.date, i18n.language)}</span>
                    <StatutDocumentBadge statut={statut} />
                    <span className="text-xs text-warmgray">
                      {t("historiqueDossier.nombreArguments", { count: a.arguments.length })}
                    </span>
                    {a.points_attention.length > 0 && (
                      <span className="badge border-risk-high/30 bg-risk-high/10 text-risk-high">{t("historiqueDossier.nombrePointsAttention", { count: a.points_attention.length })}</span>
                    )}
                  </div>
                );
              })(),
              content: (
                <div className="space-y-4">
                  <StatutDocumentMenu
                    statut={statuts[a.id] ?? a.statut}
                    loading={statutEnCours === a.id}
                    onChange={(statut) => changerStatut(a.id, statut)}
                  />
                  {a.arguments.map((arg, i) => (
                    <ArgumentCard key={i} argument={arg} index={i} />
                  ))}
                  {a.points_attention.length > 0 && (
                    <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-4">
                      <p className="mb-2 text-sm font-semibold text-risk-high">⚠ {t("planTimeline.pointsAttention")}</p>
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
