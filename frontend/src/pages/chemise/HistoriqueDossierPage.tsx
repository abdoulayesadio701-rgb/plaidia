/**
 * HistoriqueDossierPage — /chemise/historique. Fiche du dossier actif
 * (faits, parties, domaine) + historique de ses analyses de conclusions en
 * accordéon (une analyse par ligne enregistrée via /arsenal/analyser, voir
 * GET /api/dossiers/{id}/analyses).
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, dossiers as dossiersApi, downloadBlob } from "@/api";
import type { ResultatRechercheContenu, StatutDocument } from "@/api";
import { chat as chatApi } from "@/api";
import { useAlertesArticlesDossier, useAppStore, useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { CHEMIN_PAR_FEATURE } from "@/config/cheminsDocuments";
import { Link } from "react-router-dom";
import ArgumentCard from "@/components/ArgumentCard";
import Accordion from "@/components/Accordion";
import Button from "@/components/Button";
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

const CODES_LIBELLES: Record<string, string> = {
  CP: "Code pénal", CCIV: "Code civil", CPC: "Code de procédure civile",
  CPP: "Code de procédure pénale", CTRAV: "Code du travail", CCOM: "Code de commerce",
};

export default function HistoriqueDossierPage() {
  const { t, i18n } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const alertesArticles = useAlertesArticlesDossier(dossierActif?.id);
  const acquitterAlerteLoi = useAppStore((s) => s.acquitterAlerteLoi);
  const [statuts, setStatuts] = useState<Record<number, StatutDocument>>({});
  const [statutEnCours, setStatutEnCours] = useState<number | null>(null);
  const [exportEnCours, setExportEnCours] = useState(false);
  const [rechercheTexte, setRechercheTexte] = useState("");
  const [rechercheResultats, setRechercheResultats] = useState<ResultatRechercheContenu[] | null>(null);
  const [rechercheEnCours, setRechercheEnCours] = useState(false);

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

  const exporter = async () => {
    if (!dossierActif) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await dossiersApi.exporterHistorique(dossierActif.id);
      downloadBlob(blob, filename ?? "historique.docx");
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  // Recherche transversale (plan/simulateur/résumé/chronologie/vérification
  // procédurale/note client/analyses/notes) -- débounce simple, pas de
  // hook dédié pour un seul usage. Voir
  // notes/idee_2026-09-18_recherche-transversale-dossier.md pour les choix
  // de portée (plein texte), de tri (date décroissante par groupe) et de
  // visibilité (aucune restriction par rôle).
  useEffect(() => {
    if (!dossierActif) return;
    const terme = rechercheTexte.trim();
    if (!terme) {
      setRechercheResultats(null);
      setRechercheEnCours(false);
      return;
    }
    setRechercheEnCours(true);
    const minuteur = setTimeout(() => {
      dossiersApi
        .rechercherDansDossier(dossierActif.id, terme)
        .then(setRechercheResultats)
        .catch(() => setRechercheResultats([]))
        .finally(() => setRechercheEnCours(false));
    }, 300);
    return () => clearTimeout(minuteur);
  }, [rechercheTexte, dossierActif]);

  if (!dossierActif) {
    return <EmptyState titre={t("historiqueDossier.emptyTitre")} description={t("historiqueDossier.emptyDescription")} />;
  }

  // Regroupé par feature en préservant l'ordre (déjà trié par date
  // décroissante côté backend, donc chaque groupe reste trié par date
  // décroissante -- voir décision 2 de la note d'idée).
  const rechercheGroupes: [string, ResultatRechercheContenu[]][] = [];
  if (rechercheResultats) {
    for (const r of rechercheResultats) {
      const groupe = rechercheGroupes.find(([feature]) => feature === r.feature);
      if (groupe) groupe[1].push(r);
      else rechercheGroupes.push([r.feature, [r]]);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="kicker">{t("nav.sections.chemise")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{dossierActif.nom}</h1>
          <Link to={`/app/chat?dossier_id=${dossierActif.id}`} className="btn-secondary mt-3 inline-flex">
            {t("historiqueDossier.ouvrirChat")}
          </Link>
        </div>
        <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
          ⬇ {t("arsenal.exporterWord")}
        </Button>
      </div>

      {alertesArticles.length > 0 && (
        <div className="card space-y-3 border-risk-high/40 bg-risk-high/5 p-5">
          <p className="text-sm font-medium text-risk-high">
            ⚠️ {t("historiqueDossier.alerteArticlesModifies", { count: alertesArticles.length })}
          </p>
          <ul className="space-y-2">
            {alertesArticles.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <span className="text-ivory">
                  {t("historiqueDossier.articleModifie", {
                    numero: a.numero,
                    code: CODES_LIBELLES[a.code] ?? a.code,
                    ancien: a.ancien_etat ?? "?",
                    nouvel: a.nouvel_etat ?? "?",
                  })}
                </span>
                <span className="flex items-center gap-2">
                  {a.lien_source && (
                    <a href={a.lien_source} target="_blank" rel="noreferrer" className="text-xs text-amethyst-400 hover:underline">
                      {t("historiqueDossier.voirAJour")}
                    </a>
                  )}
                  <button
                    onClick={() => void acquitterAlerteLoi(a.id)}
                    className="rounded-md px-2 py-1 text-xs text-muted hover:text-ivory"
                  >
                    {t("historiqueDossier.vuIgnorer")}
                  </button>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

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

      <div className="card space-y-3 p-6">
        <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{t("historiqueDossier.rechercheTitre")}</p>
        <input
          type="search"
          className="input"
          placeholder={t("historiqueDossier.recherchePlaceholder")}
          value={rechercheTexte}
          onChange={(e) => setRechercheTexte(e.target.value)}
        />
        {rechercheEnCours && <p className="text-xs text-muted">{t("historiqueDossier.rechercheEnCours")}</p>}
        {!rechercheEnCours && rechercheResultats && rechercheResultats.length === 0 && (
          <p className="text-xs text-muted">{t("historiqueDossier.rechercheAucunResultat")}</p>
        )}
        {!rechercheEnCours && rechercheGroupes.length > 0 && (
          <div className="space-y-4">
            {rechercheGroupes.map(([feature, resultats]) => (
              <div key={feature}>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gold-500">
                  {t(`historiqueDossier.rechercheGroupe.${feature}`, feature)}
                </p>
                <div className="space-y-2">
                  {resultats.map((r) => {
                    const chemin = CHEMIN_PAR_FEATURE[r.feature as keyof typeof CHEMIN_PAR_FEATURE] ?? "grimoire/jurisprudence";
                    const lien = r.source === "document_genere" ? `/app/${chemin}?document_id=${r.id}` : `/app/${chemin}`;
                    return (
                      <Link
                        key={`${r.source}-${r.id}`}
                        to={lien}
                        className="card block space-y-1 p-3 transition-colors hover:border-gold-500/40"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className="truncate text-sm font-medium text-ivory">{r.titre}</span>
                          <span className="shrink-0 text-xs text-muted">{formaterDate(r.date, i18n.language)}</span>
                        </div>
                        <p className="truncate text-xs text-warmgray">{r.extrait}</p>
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
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
              const chemin =
                CHEMIN_PAR_FEATURE[document.feature as keyof typeof CHEMIN_PAR_FEATURE] ?? "grimoire/jurisprudence";
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
