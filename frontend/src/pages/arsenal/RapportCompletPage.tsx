/**
 * RapportCompletPage — /arsenal/rapport-complet. Le plan (optionnel) et le
 * simulateur sont lancés en parallèle côté serveur (voir
 * backend/app/routers/analyse.py::rapport_complet, ThreadPoolExecutor) —
 * un seul appel API ici, pas de Promise.all côté front à gérer.
 */

import { useState } from "react";
import { analyse as analyseApi, downloadBlob } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import DureeSlider from "@/components/DureeSlider";
import Tabs from "@/components/Tabs";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import LabeledField from "@/components/LabeledField";
import ArgumentCard from "@/components/ArgumentCard";
import PlanTimeline from "@/components/PlanTimeline";
import { SkeletonList } from "@/components/Skeleton";

const ONGLETS = [
  { id: "analyse", label: "Analyse" },
  { id: "plan", label: "Plan" },
  { id: "simulateur", label: "Simulateur" },
];

export default function RapportCompletPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [inclurePlan, setInclurePlan] = useState(true);
  const [duree, setDuree] = useState(15);
  const [ongletActif, setOngletActif] = useState("analyse");
  const [exportEnCours, setExportEnCours] = useState(false);

  const { data, loading, error, executer } = useLazyAction((d?: number) => analyseApi.rapportComplet(dossierActif!.id, d));

  const lancer = () => void executer(inclurePlan ? duree : undefined);

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await analyseApi.exporterRapportComplet(dossierActif.id, data.analyse ?? null, data.plan ?? null, data.simulateur);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_rapport_complet.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'export.");
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour générer un rapport complet." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">L'Arsenal</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Rapport complet</h1>
        <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
      </div>

      <div className="card space-y-5 p-6">
        <label className="flex items-center gap-2.5 text-sm text-warmgray">
          <input
            type="checkbox"
            checked={inclurePlan}
            onChange={(e) => setInclurePlan(e.target.checked)}
            className="h-4 w-4 rounded accent-amethyst-400"
          />
          Inclure un plan de plaidoirie chronométré
        </label>
        {inclurePlan && <DureeSlider valeur={duree} onChange={setDuree} />}
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} onClick={lancer}>
            Générer le rapport complet
          </Button>
        </div>
      </div>

      {loading && (
        <div className="space-y-3">
          <p className="text-sm text-warmgray">Génération du plan et du simulateur en parallèle…</p>
          <SkeletonList count={2} />
        </div>
      )}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Tabs tabs={ONGLETS} actif={ongletActif} onChange={setOngletActif} />
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ Exporter en Word
            </Button>
          </div>

          {ongletActif === "analyse" &&
            (data.analyse ? (
              <div className="space-y-5">
                {data.analyse.arguments.map((arg, i) => (
                  <ArgumentCard key={i} argument={arg} index={i} />
                ))}
                {data.analyse.points_attention.length > 0 && (
                  <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
                    <p className="mb-2 text-sm font-semibold text-risk-high">⚠ Points d'attention</p>
                    <ul className="space-y-1.5">
                      {data.analyse.points_attention.map((p, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-risk-high">•</span>
                          <RichOutput texte={p} prose={false} className="flex-1 text-sm" />
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <EmptyState
                titre="Aucune analyse enregistrée"
                description="Ce dossier n'a pas encore d'analyse de conclusions adverses enregistrée – utilisez « Analyser des conclusions adverses » d'abord."
              />
            ))}

          {ongletActif === "plan" &&
            (data.plan ? (
              <PlanTimeline plan={data.plan} />
            ) : (
              <EmptyState
                titre="Aucun plan généré"
                description="Cochez « Inclure un plan de plaidoirie » ci-dessus puis relancez pour en générer un."
              />
            ))}

          {ongletActif === "simulateur" && (
            <div className="space-y-4">
              {data.simulateur.objections.map((obj, i) => (
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
                  <LabeledField label="Piège" texte={obj.piege} />
                  <LabeledField label="Piste de réponse" texte={obj.piste_reponse} />
                </div>
              ))}
              {data.simulateur.point_le_plus_faible && (
                <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
                  <p className="mb-2 text-sm font-semibold text-risk-high">⚠ Point le plus faible du dossier</p>
                  <RichOutput texte={data.simulateur.point_le_plus_faible} prose={false} className="text-sm" />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre="Prêt à générer"
          description="Lance en parallèle le plan de plaidoirie (optionnel) et le simulateur d'objections, avec la dernière analyse déjà enregistrée pour ce dossier."
        />
      )}
    </div>
  );
}
