/**
 * ChronologiePage — /greffier/chronologie. Timeline verticale des
 * événements datés du dossier actif, période couverte, éléments manquants.
 * Verticale plutôt qu'horizontale : cohérent avec PlanTimeline et
 * l'accordéon d'historique de La Chemise (même vocabulaire visuel dans
 * toute l'app), et lisible sans limite de largeur pour un nombre
 * d'événements variable.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { greffier as greffierApi, downloadBlob } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

export default function ChronologiePage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [exportEnCours, setExportEnCours] = useState(false);
  const { data, loading, error, executer, definirDonnees } = useLazyAction(() => greffierApi.chronologie(dossierActif!.id));

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await greffierApi.exporterChronologie(dossierActif.id, data);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_chronologie.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("chronologie.emptyTitre")} description={t("chronologie.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{t("nav.espace.greffier")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.greffier.chronologie")}</h1>
          <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {data && (
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
          )}
          <Button variant="primary" loading={loading} onClick={() => void executer()}>
            {data ? `↻ ${t("noteClient.regenerer")}` : t("chronologie.construire")}
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-6">
          <p className="flex items-center gap-2 text-sm text-warmgray">
            {t("chronologie.periodeCouverte")}
            <span className="badge border-amethyst-400/40 bg-amethyst-400/10 text-amethyst-400">{data.periode_couverte}</span>
          </p>

          {data.evenements.length === 0 ? (
            <EmptyState titre={t("chronologie.aucunEvenementTitre")} description={t("chronologie.aucunEvenementDescription")} />
          ) : (
            <div className="relative space-y-5 border-l-2 border-gold-600/25 pl-8">
              {data.evenements.map((ev, i) => (
                <div key={i} className="relative">
                  <span className="absolute -left-[38px] flex h-6 w-6 items-center justify-center rounded-pill border-2 border-gold-600 bg-void font-mono text-xs text-gold-500">
                    {i + 1}
                  </span>
                  <div className="card space-y-1 p-4">
                    <p className="font-mono text-xs font-semibold text-amethyst-400">{ev.date}</p>
                    <p className="text-sm text-ivory">{ev.evenement}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {data.elements_manquants.length > 0 && (
            <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-5">
              <p className="mb-2 text-sm font-semibold text-gold-500">{t("resumerDossier.elementsManquants")}</p>
              <ul className="space-y-1.5 text-sm text-ivory">
                {data.elements_manquants.map((el, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-gold-500">•</span>
                    {el}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <ChatContextuelPanel
            feature="chronologie"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            placeholder={t("chronologie.chatPlaceholder")}
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre={t("chronologie.pretTitre")} description={t("chronologie.pretDescription")} />
      )}
    </div>
  );
}
