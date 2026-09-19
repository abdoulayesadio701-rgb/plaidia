/**
 * ResumerDossierPage — /arsenal/resumer. Ne nécessite que le dossier actif
 * (aucune saisie), mais reste déclenché par un clic explicite plutôt
 * qu'auto-lancé à la navigation — même règle que tout l'Arsenal, un appel
 * IA a un coût réel, jamais silencieux.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, downloadBlob } from "@/api";
import type { ResumeResultat } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useDernierDocumentGenere } from "@/hooks/useDernierDocumentGenere";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";
import ConfirmerModal from "@/components/ConfirmerModal";

export default function ResumerDossierPage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);
  const [exportEnCours, setExportEnCours] = useState(false);
  const { data, loading, error, executer, definirDonnees, reinitialiser } = useLazyAction(() => analyseApi.resumerDossier(dossierActif!.id));
  // Recharge automatiquement, au montage, le dernier résumé déjà persisté
  // pour ce dossier -- une simple lecture, jamais un nouvel appel IA -- pour
  // qu'il reste visible après une navigation ou un refresh complet.
  const { document: dernierDocument, loading: dernierDocumentLoading } = useDernierDocumentGenere(dossierActif?.id, "resume");

  useEffect(() => {
    if (!dernierDocument || data) return;
    definirDonnees({ ...(dernierDocument.contenu as unknown as ResumeResultat), document_id: dernierDocument.id, statut: dernierDocument.statut });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dernierDocument]);

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await analyseApi.exporterResume(dossierActif.id, data);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_resume.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  const supprimer = async () => {
    if (!data?.document_id) return;
    setSuppressionEnCours(true);
    try {
      await analyseApi.supprimerDocumentGenere(data.document_id);
      reinitialiser();
      setConfirmationSuppression(false);
      pousserToast("success", t("arsenal.resultatSupprime"));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurSuppression"));
    } finally {
      setSuppressionEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("resumerDossier.emptyTitre")} description={t("resumerDossier.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="kicker">{t("nav.sections.arsenal")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.arsenal.resumer")}</h1>
          <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
        </div>
        {data && (
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
            <Button variant="ghost" loading={loading} onClick={() => void executer()}>
              🔄 {t("simulateur.relancer")}
            </Button>
            {data.document_id && (
              <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
            )}
          </div>
        )}
      </div>

      {!data && !loading && !dernierDocumentLoading && !error && (
        <EmptyState
          titre={t("resumerDossier.pretTitre")}
          description={t("resumerDossier.pretDescription")}
          action={
            <Button variant="primary" onClick={() => void executer()}>
              {t("nav.arsenal.resumer")}
            </Button>
          }
        />
      )}

      {(loading || dernierDocumentLoading) && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !dernierDocumentLoading && !error && data && (
        <div className="space-y-5">
          <div className="card p-6">
            <p className="kicker">{t("resumerDossier.resume")}</p>
            <RichOutput texte={data.resume_court} className="mt-3" />
          </div>

          {data.points_cles.length > 0 && (
            <div className="card p-6">
              <p className="mb-3 text-micro font-medium uppercase tracking-wide text-gold-500">{t("resumerDossier.pointsCles")}</p>
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
              <p className="mb-2 text-sm font-semibold text-gold-500">{t("resumerDossier.elementsManquants")}</p>
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
            placeholder={t("resumerDossier.chatPlaceholder")}
          />
        </div>
      )}

      {confirmationSuppression && (
        <ConfirmerModal
          titre={t("arsenal.confirmerSuppressionTitre")}
          description={t("arsenal.confirmerSuppressionDescription")}
          texteBouton={t("commun.supprimer")}
          enCours={suppressionEnCours}
          onFermer={() => setConfirmationSuppression(false)}
          onConfirmer={supprimer}
        />
      )}
    </div>
  );
}
