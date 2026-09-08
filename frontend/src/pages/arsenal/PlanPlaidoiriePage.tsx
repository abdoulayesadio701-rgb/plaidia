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

import { useState } from "react";
import { useLocation } from "react-router-dom";
import { analyse as analyseApi, downloadBlob } from "@/api";
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

interface NavigationState {
  dureeMinutesPreremplie?: number;
}

export default function PlanPlaidoiriePage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const location = useLocation();
  const dureeInitiale = (location.state as NavigationState | null)?.dureeMinutesPreremplie ?? 15;

  const [duree, setDuree] = useState(dureeInitiale);
  const [exportEnCours, setExportEnCours] = useState(false);

  const { data, loading, error, executer, definirDonnees } = useLazyAction((d: number) => analyseApi.genererPlan(dossierActif!.id, d));

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

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer(duree)} />}

      {!loading && !error && data && (
        <div className="space-y-6">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-warmgray">Plan généré pour {duree} min de parole.</p>
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ Exporter en Word
            </Button>
          </div>

          <PlanTimeline plan={data} />

          <VerificationPanel verification={data.verification} />

          <ChatContextuelPanel
            feature="plan"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
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
