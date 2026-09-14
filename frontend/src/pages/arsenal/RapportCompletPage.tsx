/**
 * RapportCompletPage — /arsenal/rapport-complet. Le plan (optionnel) et le
 * simulateur sont lancés en parallèle côté serveur (voir
 * backend/app/routers/analyse.py::rapport_complet, ThreadPoolExecutor) —
 * un seul appel API ici, pas de Promise.all côté front à gérer.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
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
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

export default function RapportCompletPage() {
  const { t } = useTranslation();
  const ONGLETS = [
    { id: "analyse", label: t("rapportComplet.ongletAnalyse") },
    { id: "plan", label: t("rapportComplet.ongletPlan") },
    { id: "simulateur", label: t("rapportComplet.ongletSimulateur") },
  ];
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [inclurePlan, setInclurePlan] = useState(true);
  const [duree, setDuree] = useState(15);
  const [ongletActif, setOngletActif] = useState("analyse");
  const [exportEnCours, setExportEnCours] = useState(false);

  const { data, loading, error, executer, definirDonnees } = useLazyAction((d?: number) => analyseApi.rapportComplet(dossierActif!.id, d));

  const lancer = () => void executer(inclurePlan ? duree : undefined);

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await analyseApi.exporterRapportComplet(dossierActif.id, data.analyse ?? null, data.plan ?? null, data.simulateur);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_rapport_complet.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("rapportComplet.emptyTitre")} description={t("rapportComplet.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.arsenal")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.arsenal.rapport-complet")}</h1>
        <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
      </div>

      <div className="card space-y-5 p-6">
        <label className="flex items-center gap-2.5 text-sm text-warmgray">
          <input
            type="checkbox"
            checked={inclurePlan}
            onChange={(e) => setInclurePlan(e.target.checked)}
            className="h-4 w-4 rounded accent-amethyst-400"
          />
          {t("rapportComplet.inclurePlan")}
        </label>
        {inclurePlan && <DureeSlider valeur={duree} onChange={setDuree} />}
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} onClick={lancer}>
            {t("rapportComplet.generer")}
          </Button>
        </div>
      </div>

      {loading && (
        <div className="space-y-3">
          <p className="text-sm text-warmgray">{t("rapportComplet.generationEnParallele")}</p>
          <SkeletonList count={2} />
        </div>
      )}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Tabs tabs={ONGLETS} actif={ongletActif} onChange={setOngletActif} />
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
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
                    <p className="mb-2 text-sm font-semibold text-risk-high">⚠ {t("planTimeline.pointsAttention")}</p>
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
                <ChatContextuelPanel
                  feature="conclusions"
                  resultatActuel={data.analyse}
                  onMiseAJour={(nouveau) => definirDonnees({ ...data, analyse: nouveau })}
                  dossierId={dossierActif.id}
                />
              </div>
            ) : (
              <EmptyState
                titre={t("rapportComplet.aucuneAnalyseTitre")}
                description={t("rapportComplet.aucuneAnalyseDescription")}
              />
            ))}

          {ongletActif === "plan" &&
            (data.plan ? (
              <div className="space-y-5">
                <PlanTimeline plan={data.plan} />
                <ChatContextuelPanel
                  feature="plan"
                  resultatActuel={data.plan}
                  onMiseAJour={(nouveau) => definirDonnees({ ...data, plan: nouveau })}
                  dossierId={dossierActif.id}
                />
              </div>
            ) : (
              <EmptyState
                titre={t("rapportComplet.aucunPlanTitre")}
                description={t("rapportComplet.aucunPlanDescription")}
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
                  <LabeledField label={t("simulateur.piege")} texte={obj.piege} />
                  <LabeledField label={t("simulateur.pisteReponse")} texte={obj.piste_reponse} />
                </div>
              ))}
              {data.simulateur.point_le_plus_faible && (
                <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
                  <p className="mb-2 text-sm font-semibold text-risk-high">⚠ {t("simulateur.pointLePlusFaible")}</p>
                  <RichOutput texte={data.simulateur.point_le_plus_faible} prose={false} className="text-sm" />
                </div>
              )}
              <ChatContextuelPanel
                feature="simulateur"
                resultatActuel={data.simulateur}
                onMiseAJour={(nouveau) => definirDonnees({ ...data, simulateur: nouveau })}
                dossierId={dossierActif.id}
              />
            </div>
          )}
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre={t("rapportComplet.pretTitre")}
          description={t("rapportComplet.pretDescription")}
        />
      )}
    </div>
  );
}
