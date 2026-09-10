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

import { useEffect, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import { analyse as analyseApi, downloadBlob } from "@/api";
import type { PlanResultat, StatutDocument } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import DureeSlider from "@/components/DureeSlider";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import PlanTimeline from "@/components/PlanTimeline";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";
import VerificationPanel from "@/components/VerificationPanel";
import StatutDocumentMenu, { StatutDocumentBadge } from "@/components/StatutDocument";
import PinButton from "@/components/PinButton";
import { useAsync } from "@/hooks/useAsync";

interface NavigationState {
  dureeMinutesPreremplie?: number;
}

export default function PlanPlaidoiriePage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const dureeInitiale = (location.state as NavigationState | null)?.dureeMinutesPreremplie ?? 15;

  const [duree, setDuree] = useState(dureeInitiale);
  const [exportEnCours, setExportEnCours] = useState(false);
  const [statutEnCours, setStatutEnCours] = useState(false);
  const documentId = Number(searchParams.get("document_id"));
  const aDocument = Number.isInteger(documentId) && documentId > 0;

  const { data, loading, error, executer, definirDonnees } = useLazyAction((d: number) => analyseApi.genererPlan(dossierActif!.id, d));
  const { data: document, loading: documentLoading, error: documentError } = useAsync(
    () => analyseApi.obtenirDocumentGenere(documentId),
    [documentId, dossierActif?.id],
    aDocument && dossierActif !== null
  );

  useEffect(() => {
    if (!document || document.feature !== "plan" || document.dossier_id !== dossierActif?.id) return;
    definirDonnees({ ...(document.contenu as unknown as PlanResultat), document_id: document.id, statut: document.statut });
    const minutes = document.parametres.temps_minutes;
    if (typeof minutes === "number") setDuree(minutes);
  }, [document, dossierActif?.id, definirDonnees]);

  const changerStatut = async (statut: StatutDocument) => {
    if (!data?.document_id) return;
    setStatutEnCours(true);
    try {
      await analyseApi.changerStatutDocument(data.document_id, statut);
      definirDonnees({ ...data, statut });
      pousserToast("success", `Document passé au statut « ${statut} ».`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Impossible de changer le statut.");
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
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'export.");
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour générer un plan de plaidoirie." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">L'Arsenal</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Générer un plan de plaidoirie</h1>
        <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
      </div>

      <div className="card space-y-5 p-6">
        <DureeSlider valeur={duree} onChange={setDuree} />
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} onClick={() => void executer(duree)}>
            Générer le plan
          </Button>
        </div>
      </div>

      {(loading || documentLoading) && <SkeletonList count={2} />}

      {!loading && !documentLoading && (error || documentError) && <ErrorState message={error ?? documentError ?? "Erreur de chargement."} onRetry={() => void executer(duree)} />}

      {!loading && !documentLoading && !error && !documentError && data && (
        <div className="space-y-6">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2"><p className="text-sm text-warmgray">Plan généré pour {duree} min de parole.</p><StatutDocumentBadge statut={data.statut ?? "Brouillon"} /></div>
            <div className="flex items-center gap-2"><StatutDocumentMenu statut={data.statut ?? "Brouillon"} loading={statutEnCours} onChange={changerStatut} /><PinButton type="document_genere" referenceId={data.document_id!} dossierId={dossierActif.id} libelle={`Plan — ${dossierActif.nom}`} /><Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>⬇ Exporter en Word</Button></div>
          </div>

          <PlanTimeline plan={data} />

          <VerificationPanel verification={data.verification} />

          <ChatContextuelPanel
            feature="plan"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            documentId={data.document_id}
            placeholder="Ex. « Rends l'accroche plus percutante », « adapte le ton pour une audience pénale »…"
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à générer" description="Réglez le temps de parole ci-dessus puis cliquez sur « Générer le plan »." />
      )}
    </div>
  );
}
