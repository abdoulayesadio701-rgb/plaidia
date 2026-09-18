/**
 * PlanPlaidoiriePage — /arsenal/plan. La durée peut arriver préremplie
 * via la barre de commande (CommandBar navigue avec
 * `state: { dureeMinutesPreremplie }`, voir router.tsx).
 *
 * Export : réutilise POST /api/analyse/rapport-complet/export avec
 * `analyse` et `simulateur` à null — le backend (export.py) rend chaque
 * section du docx uniquement si elle est fournie, donc ce même endpoint
 * produit un .docx ne contenant que le plan, sans doublon de code.
 * Limite honnête : cet endpoint ne produit que du Word, pas de PDF — voir
 * le récapitulatif envoyé après cette implémentation.
 */

import { useCallback, useEffect, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, downloadBlob } from "@/api";
import type { PlanResultat, StatutDocument } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyStream } from "@/hooks/useLazyStream";
import Button from "@/components/Button";
import DureeSlider from "@/components/DureeSlider";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import EtapePipelineIndicator from "@/components/EtapePipelineIndicator";
import PlanTimeline from "@/components/PlanTimeline";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";
import VerificationPanel from "@/components/VerificationPanel";
import StatutDocumentMenu, { StatutDocumentBadge } from "@/components/StatutDocument";
import ConfirmerModal from "@/components/ConfirmerModal";
import { useAsync } from "@/hooks/useAsync";
import { useDernierDocumentGenere } from "@/hooks/useDernierDocumentGenere";

interface NavigationState {
  dureeMinutesPreremplie?: number;
}

export default function PlanPlaidoiriePage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const dureeInitiale = (location.state as NavigationState | null)?.dureeMinutesPreremplie ?? 15;

  const [duree, setDuree] = useState(dureeInitiale);
  const [exportEnCours, setExportEnCours] = useState(false);
  const [statutEnCours, setStatutEnCours] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);
  const documentId = Number(searchParams.get("document_id"));
  const aDocument = Number.isInteger(documentId) && documentId > 0;

  const lancerFlux = useCallback(
    (d: number, cb: Parameters<typeof analyseApi.streamGenererPlan>[2], signal: AbortSignal) =>
      analyseApi.streamGenererPlan(dossierActif!.id, d, cb, signal),
    [dossierActif]
  );
  const { data, etape, loading, error, executer, definirDonnees, reinitialiser } = useLazyStream<PlanResultat, [number]>(lancerFlux);
  // Lien explicite depuis l'Historique (?document_id=X) : prioritaire sur
  // l'auto-chargement du plus récent ci-dessous.
  const { data: document, loading: documentLoading, error: documentError } = useAsync(
    () => analyseApi.obtenirDocumentGenere(documentId),
    [documentId, dossierActif?.id],
    aDocument && dossierActif !== null
  );
  // Sans lien explicite : recharge automatiquement le dernier plan généré
  // pour ce dossier -- une simple lecture, jamais un nouvel appel IA -- pour
  // qu'il reste visible après une navigation ou un refresh complet.
  const { document: dernierDocument, loading: dernierDocumentLoading } = useDernierDocumentGenere(
    dossierActif?.id,
    "plan",
    !aDocument
  );

  useEffect(() => {
    const source = aDocument ? document : dernierDocument;
    if (!source || source.feature !== "plan" || source.dossier_id !== dossierActif?.id) return;
    definirDonnees({ ...(source.contenu as unknown as PlanResultat), document_id: source.id, statut: source.statut });
    const minutes = source.parametres.temps_minutes;
    if (typeof minutes === "number") setDuree(minutes);
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
      const { blob, filename } = await analyseApi.exporterRapportComplet(dossierActif.id, null, data, null);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_plan.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("planPlaidoirie.emptyTitre")} description={t("planPlaidoirie.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.arsenal")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.arsenal.plan")}</h1>
        <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
      </div>

      <div className="card space-y-5 p-6">
        <DureeSlider valeur={duree} onChange={setDuree} />
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} onClick={() => void executer(duree)}>
            {t("planPlaidoirie.generer")}
          </Button>
        </div>
      </div>

      {(loading && !data?.plan) || documentLoading || dernierDocumentLoading ? <SkeletonList count={2} /> : null}

      {loading && <EtapePipelineIndicator etape={etape} />}

      {!loading && !documentLoading && (error || documentError) && <ErrorState message={error ?? documentError ?? t("arsenal.erreurChargement")} onRetry={() => void executer(duree)} />}

      {!documentLoading && !dernierDocumentLoading && !error && !documentError && data?.plan && (
        <div className="space-y-6">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2"><p className="text-sm text-warmgray">{t("planPlaidoirie.genereePour", { duree })}</p><StatutDocumentBadge statut={data.statut ?? "Brouillon"} /></div>
            <div className="flex items-center gap-2">
              <StatutDocumentMenu statut={data.statut ?? "Brouillon"} loading={statutEnCours} onChange={changerStatut} />
              <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>⬇ {t("arsenal.exporterWord")}</Button>
              {data.document_id && (
                <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
              )}
            </div>
          </div>

          <PlanTimeline plan={data} />

          {data.diagnostic && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">{t("arsenal.diagnostic")}</h2><p className="whitespace-pre-wrap text-sm text-warmgray">{data.diagnostic}</p></div>}
          {data.strategie && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">{t("arsenal.strategie")}</h2><p className="whitespace-pre-wrap text-sm text-ivory">{data.strategie}</p></div>}

          <VerificationPanel verification={data.verification} />

          <ChatContextuelPanel
            feature="plan"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            documentId={data.document_id}
            placeholder={t("planPlaidoirie.chatPlaceholder")}
          />
        </div>
      )}

      {!loading && !documentLoading && !dernierDocumentLoading && !error && !data?.plan && (
        <EmptyState titre={t("planPlaidoirie.pretTitre")} description={t("planPlaidoirie.pretDescription")} />
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
