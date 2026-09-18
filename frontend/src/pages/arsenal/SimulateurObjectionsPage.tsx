/**
 * SimulateurObjectionsPage — /arsenal/simulateur. Mode "entraînement" :
 * masque la piste de réponse jusqu'au clic, pour répéter à l'oral sans se
 * la faire souffler — désactiver le mode l'affiche tout de suite (relecture).
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, downloadBlob } from "@/api";
import type { SimulateurResultat, StatutDocument } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import LabeledField from "@/components/LabeledField";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";
import VerificationPanel from "@/components/VerificationPanel";
import StatutDocumentMenu, { StatutDocumentBadge } from "@/components/StatutDocument";
import ConfirmerModal from "@/components/ConfirmerModal";
import { useAsync } from "@/hooks/useAsync";
import { useDernierDocumentGenere } from "@/hooks/useDernierDocumentGenere";

export default function SimulateurObjectionsPage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const [searchParams] = useSearchParams();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [modeEntrainement, setModeEntrainement] = useState(false);
  const [revelees, setRevelees] = useState<Set<number>>(new Set());
  const [exportEnCours, setExportEnCours] = useState(false);
  const [statutEnCours, setStatutEnCours] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);
  const documentId = Number(searchParams.get("document_id"));
  const aDocument = Number.isInteger(documentId) && documentId > 0;

  const { data, loading, error, executer, definirDonnees, reinitialiser } = useLazyAction(() => analyseApi.simulerObjections(dossierActif!.id));
  const { data: document, loading: documentLoading, error: documentError } = useAsync(
    () => analyseApi.obtenirDocumentGenere(documentId),
    [documentId, dossierActif?.id],
    aDocument && dossierActif !== null
  );
  const { document: dernierDocument, loading: dernierDocumentLoading } = useDernierDocumentGenere(
    dossierActif?.id,
    "simulateur",
    !aDocument
  );

  useEffect(() => {
    const source = aDocument ? document : dernierDocument;
    if (!source || source.feature !== "simulateur" || source.dossier_id !== dossierActif?.id) return;
    definirDonnees({ ...(source.contenu as unknown as SimulateurResultat), document_id: source.id, statut: source.statut });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [document, dernierDocument, aDocument, dossierActif?.id, definirDonnees]);

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

  const changerStatut = async (statut: StatutDocument) => {
    if (!data?.document_id) return;
    setStatutEnCours(true);
    try {
      await analyseApi.changerStatutDocument(data.document_id, statut);
      definirDonnees({ ...data, statut });
      pousserToast("success", t("statutDocument.changePousse", { statut: t(`statutDocument.${statut}`, statut) }));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurChangementStatut"));
    } finally {
      setStatutEnCours(false);
    }
  };

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await analyseApi.exporterSimulateur(dossierActif.id, data);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_simulateur.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  const basculerEntrainement = () => {
    setModeEntrainement((v) => !v);
    setRevelees(new Set()); // repart de zéro à chaque bascule -- l'entraînement recommence masqué
  };

  const reveler = (i: number) => setRevelees((prev) => new Set(prev).add(i));

  if (!dossierActif) {
    return <EmptyState titre={t("simulateur.emptyTitre")} description={t("simulateur.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="kicker">{t("nav.sections.arsenal")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.arsenal.simulateur")}</h1>
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

      {!data && !loading && !documentLoading && !dernierDocumentLoading && !error && (
        <EmptyState
          titre={t("simulateur.pretTitre")}
          description={t("simulateur.pretDescription")}
          action={
            <Button variant="primary" onClick={() => void executer()}>
              {t("simulateur.simuler")}
            </Button>
          }
        />
      )}

      {(loading || documentLoading || dernierDocumentLoading) && <SkeletonList count={3} />}

      {!loading && !documentLoading && (error || documentError) && <ErrorState message={error ?? documentError ?? t("arsenal.erreurChargement")} onRetry={() => void executer()} />}

      {!loading && !documentLoading && !dernierDocumentLoading && !error && !documentError && data && (
        <div className="space-y-5">
          <div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2"><span className="text-sm text-warmgray">{t("simulateur.documentSauvegarde")}</span><StatutDocumentBadge statut={data.statut ?? "Brouillon"} /></div><StatutDocumentMenu statut={data.statut ?? "Brouillon"} loading={statutEnCours} onChange={changerStatut} /></div>
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
            {t("simulateur.modeEntrainement")}
          </label>

          {data.objections.length === 0 ? (
            <EmptyState titre={t("simulateur.aucuneObjectionTitre")} description={t("simulateur.aucuneObjectionDescription")} />
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

                    <LabeledField label={t("simulateur.piege")} texte={obj.piege} />

                    {masquee ? (
                      <Button variant="secondary" onClick={() => reveler(i)}>
                        👁 {t("simulateur.revelerPiste")}
                      </Button>
                    ) : (
                      <LabeledField label={t("simulateur.pisteReponse")} texte={obj.piste_reponse} />
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {data.point_le_plus_faible && (
            <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
              <p className="mb-2 text-sm font-semibold text-risk-high">⚠ {t("simulateur.pointLePlusFaible")}</p>
              <RichOutput texte={data.point_le_plus_faible} prose={false} className="text-sm" />
            </div>
          )}

          {data.diagnostic && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">{t("arsenal.diagnostic")}</h2><p className="whitespace-pre-wrap text-sm text-warmgray">{data.diagnostic}</p></div>}
          {data.strategie && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">{t("arsenal.strategie")}</h2><p className="whitespace-pre-wrap text-sm text-ivory">{data.strategie}</p></div>}

          <VerificationPanel verification={data.verification} />

          <ChatContextuelPanel
            feature="simulateur"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            documentId={data.document_id}
            placeholder={t("simulateur.chatPlaceholder")}
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
