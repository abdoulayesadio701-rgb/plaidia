/**
 * EntrainementPage — /arsenal/entrainement. Répétition chronométrée de la
 * plaidoirie : le plan le plus récent du dossier fournit les sections et leur
 * temps alloué (duree_minutes, déjà calculé à la génération du plan -- aucun
 * appel IA ici). Le chronomètre vit dans le navigateur ; seul le bilan est
 * envoyé au backend (POST /api/entrainement/), qui le persiste dans
 * documents_generes (feature="entrainement") et le rend exportable en Word.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, dossiers as dossiersApi, entrainement as entrainementApi, downloadBlob } from "@/api";
import type { BilanEntrainement, PlanResultat, PointPlan, SectionMesuree, StatutSectionEntrainement } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useDernierDocumentGenere } from "@/hooks/useDernierDocumentGenere";
import { formaterChrono, formaterDuree } from "@/config/durees";
import { demarrerChrono, mettreEnPause, reprendre, secondesEcoulees, type EtatChrono } from "./chronometre";
import { resumerSeances } from "./seancesEntrainement";
import Button from "@/components/Button";
import ConfirmerModal from "@/components/ConfirmerModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

type Phase = "attente" | "en_cours" | "termine";

const CLASSE_STATUT: Record<StatutSectionEntrainement, string> = {
  dans_les_temps: "badge-risk-low",
  en_avance: "badge-risk-medium",
  depasse: "badge-risk-high",
  non_traite: "badge border-muted/30 bg-surface-2 text-warmgray",
};

/** Temps alloué par section : duree_minutes du plan ; à défaut, le temps de
 * parole restant du plan (parametres.temps_minutes) est réparti à parts
 * égales entre les sections sans durée. */
function allouerSecondes(points: PointPlan[], tempsMinutes: number | undefined): number[] {
  const definies = points.reduce((somme, p) => somme + (p.duree_minutes ? p.duree_minutes * 60 : 0), 0);
  const sansDuree = points.filter((p) => !p.duree_minutes).length;
  const reste = tempsMinutes ? Math.max(0, tempsMinutes * 60 - definies) : 60 * sansDuree;
  const part = sansDuree > 0 ? Math.round(reste / sansDuree) : 0;
  return points.map((p) => (p.duree_minutes ? p.duree_minutes * 60 : part));
}

export default function EntrainementPage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === "en" ? "en-GB" : "fr-FR";
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);

  const [phase, setPhase] = useState<Phase>("attente");
  const [index, setIndex] = useState(0);
  const [mesures, setMesures] = useState<number[]>([]);
  const [maintenant, setMaintenant] = useState(() => Date.now());
  const [chrono, setChrono] = useState<EtatChrono>(() => demarrerChrono(Date.now()));
  const [sectionsMesurees, setSectionsMesurees] = useState<SectionMesuree[]>([]);
  const [exportEnCours, setExportEnCours] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);

  const { document: dernierPlan, loading: planLoading } = useDernierDocumentGenere(dossierActif?.id, "plan");
  // Toutes les séances enregistrées (la plus récente en tête) : la dernière
  // est affichée en bilan, l'ensemble sert à comparer les séances.
  const { data: documentsSeances, loading: bilanLoading, reload: rechargerSeances } = useAsync(
    () => dossiersApi.listerDocumentsGeneres(dossierActif!.id, "entrainement"),
    [dossierActif?.id],
    dossierActif !== null
  );
  const dernierBilan = documentsSeances && documentsSeances.length > 0 ? documentsSeances[0] : null;
  const seances = useMemo(() => resumerSeances(documentsSeances ?? []), [documentsSeances]);
  const { data: bilan, loading: enregistrement, error, executer, definirDonnees, reinitialiser } = useLazyAction(
    (sections: SectionMesuree[]) => entrainementApi.enregistrerBilan(dossierActif!.id, sections)
  );

  // Relit le dernier bilan persisté (simple GET) pour qu'il reste visible
  // après une navigation ou un refresh.
  useEffect(() => {
    if (!dernierBilan || bilan || phase !== "attente") return;
    definirDonnees({ ...(dernierBilan.contenu as unknown as BilanEntrainement), document_id: dernierBilan.id, statut: dernierBilan.statut });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dernierBilan]);

  useEffect(() => {
    if (phase !== "en_cours") return;
    const minuteur = setInterval(() => setMaintenant(Date.now()), 250);
    return () => clearInterval(minuteur);
  }, [phase]);

  const plan = dernierPlan ? (dernierPlan.contenu as unknown as PlanResultat) : null;
  const points = useMemo(() => plan?.plan ?? [], [plan]);
  const tempsMinutes = dernierPlan?.parametres.temps_minutes;
  const alloues = useMemo(
    () => allouerSecondes(points, typeof tempsMinutes === "number" ? tempsMinutes : undefined),
    [points, tempsMinutes]
  );

  const cloturer = (mesuresFinales: number[]) => {
    const sections: SectionMesuree[] = points.map((p, i) => ({
      point: p.point,
      alloue_secondes: alloues[i],
      reel_secondes: mesuresFinales[i] ?? 0,
      traitee: i < mesuresFinales.length,
    }));
    setSectionsMesurees(sections);
    setPhase("termine");
    void executer(sections).then((resultat) => {
      if (resultat) rechargerSeances();
    });
  };

  const ecouleActuel = () => secondesEcoulees(chrono, Date.now());

  const demarrer = () => {
    reinitialiser();
    setMesures([]);
    setIndex(0);
    setChrono(demarrerChrono(Date.now()));
    setMaintenant(Date.now());
    setPhase("en_cours");
  };

  const sectionSuivante = () => {
    const nouvelles = [...mesures, ecouleActuel()];
    setMesures(nouvelles);
    if (index + 1 < points.length) {
      setIndex(index + 1);
      setChrono(demarrerChrono(Date.now()));
      setMaintenant(Date.now());
    } else {
      cloturer(nouvelles);
    }
  };

  const arreter = () => cloturer([...mesures, ecouleActuel()]);

  const basculerPause = () => setChrono((etat) => (etat.pauseDepuis === null ? mettreEnPause(etat, Date.now()) : reprendre(etat, Date.now())));

  const exporter = async () => {
    if (!dossierActif || !bilan) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await entrainementApi.exporterBilan(dossierActif.id, bilan);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_entrainement.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  const supprimer = async () => {
    if (!bilan?.document_id) return;
    setSuppressionEnCours(true);
    try {
      await analyseApi.supprimerDocumentGenere(bilan.document_id);
      reinitialiser();
      setPhase("attente");
      setConfirmationSuppression(false);
      rechargerSeances();
      pousserToast("success", t("arsenal.resultatSupprime"));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurSuppression"));
    } finally {
      setSuppressionEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("entrainement.emptyTitre")} description={t("entrainement.emptyDescription")} />;
  }

  const chargement = planLoading || bilanLoading;
  const ecoule = phase === "en_cours" ? secondesEcoulees(chrono, maintenant) : 0;
  const enPause = chrono.pauseDepuis !== null;
  const alloueCourant = alloues[index] ?? 0;
  const ratio = alloueCourant > 0 ? ecoule / alloueCourant : 0;
  const classeChrono = ratio > 1 ? "badge-risk-high" : ratio > 0.9 ? "badge-risk-medium" : "badge-risk-low";
  const pointCourant = points[index];
  const sectionsADepasser = bilan?.sections.filter((s) => s.statut === "depasse") ?? [];
  const nonTraitees = bilan?.sections.filter((s) => s.statut === "non_traite") ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{t("nav.sections.arsenal")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.arsenal.entrainement")}</h1>
          <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
        </div>
        {bilan && phase !== "en_cours" && (
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
            {bilan.document_id && (
              <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
            )}
          </div>
        )}
      </div>

      {chargement && <SkeletonList count={2} />}

      {!chargement && points.length === 0 && (
        <EmptyState
          titre={t("entrainement.aucunPlanTitre")}
          description={t("entrainement.aucunPlanDescription")}
          action={<Link to="/app/arsenal/plan" className="btn-secondary">{t("entrainement.genererPlan")}</Link>}
        />
      )}

      {!chargement && points.length > 0 && phase === "attente" && (
        <div className="card space-y-4 p-6">
          <p className="text-sm text-warmgray">{t("entrainement.sousTitre")}</p>
          <ol className="space-y-1.5 text-sm text-ivory">
            {points.map((p, i) => (
              <li key={i} className="flex items-baseline justify-between gap-3">
                <span className="min-w-0 truncate">{i + 1}. {p.point}</span>
                <span className="shrink-0 font-mono text-xs text-muted">{formaterChrono(alloues[i])}</span>
              </li>
            ))}
          </ol>
          <div className="flex justify-end">
            <Button variant="primary" onClick={demarrer}>
              ▶ {bilan ? t("entrainement.recommencer") : t("entrainement.demarrer")}
            </Button>
          </div>
        </div>
      )}

      {phase === "en_cours" && pointCourant && (
        <div className="card space-y-5 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">
              {t("entrainement.sectionNumero", { numero: index + 1, total: points.length })}
            </p>
            <span className={`${enPause ? "badge border-muted/30 bg-surface-2 text-warmgray" : classeChrono} font-mono text-lg`} aria-live="off">
              {enPause && `⏸ ${t("entrainement.enPause")} · `}
              {formaterChrono(ecoule)} / {formaterChrono(alloueCourant)}
            </span>
          </div>
          <h2 className="font-serif text-h3 font-semibold text-ivory">{pointCourant.point}</h2>
          {pointCourant.argument_cle && (
            <div>
              <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">{t("entrainement.argumentCle")}</p>
              <p className="text-sm text-ivory">{pointCourant.argument_cle}</p>
            </div>
          )}
          {pointCourant.notes && <p className="whitespace-pre-wrap text-sm text-warmgray">{pointCourant.notes}</p>}
          <div className="flex flex-wrap justify-between gap-3">
            <div className="flex gap-2">
              <Button variant="ghost" onClick={arreter}>■ {t("entrainement.arreter")}</Button>
              <Button variant="secondary" onClick={basculerPause}>
                {enPause ? `▶ ${t("entrainement.reprendre")}` : `⏸ ${t("entrainement.pause")}`}
              </Button>
            </div>
            <Button variant="primary" onClick={sectionSuivante}>
              {index + 1 < points.length ? `${t("entrainement.sectionSuivante")} →` : `${t("entrainement.terminer")} ✓`}
            </Button>
          </div>
        </div>
      )}

      {phase === "termine" && enregistrement && <SkeletonList count={1} />}

      {phase === "termine" && !enregistrement && error && (
        <ErrorState message={error} onRetry={() => void executer(sectionsMesurees)} />
      )}

      {bilan && !enregistrement && phase !== "en_cours" && (
        <div className="space-y-4">
          <div className="overflow-x-auto rounded-md border border-gold-600/20">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-gold-600/20 bg-surface-2 text-left text-micro uppercase tracking-wide text-warmgray">
                  <th className="px-4 py-3 font-medium">{t("entrainement.colSection")}</th>
                  <th className="px-4 py-3 font-medium">{t("entrainement.colAlloue")}</th>
                  <th className="px-4 py-3 font-medium">{t("entrainement.colReel")}</th>
                  <th className="px-4 py-3 font-medium">{t("entrainement.colEcart")}</th>
                  <th className="px-4 py-3 font-medium" />
                </tr>
              </thead>
              <tbody>
                {bilan.sections.map((s, i) => (
                  <tr key={i} className="border-b border-gold-600/10 last:border-0">
                    <td className="px-4 py-3 text-ivory">{s.point}</td>
                    <td className="px-4 py-3 font-mono text-warmgray">{formaterChrono(s.alloue_secondes)}</td>
                    <td className="px-4 py-3 font-mono text-warmgray">{s.statut === "non_traite" ? "—" : formaterChrono(s.reel_secondes)}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-warmgray">{s.statut === "non_traite" ? "—" : formaterDuree(s.ecart_secondes)}</td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span className={CLASSE_STATUT[s.statut]}>{t(`entrainement.statut.${s.statut}`)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card space-y-2 p-5 text-sm text-ivory">
            <p className="font-semibold">
              {bilan.total_ecart_secondes > 0
                ? t("entrainement.syntheseDepasse", { duree: formaterDuree(bilan.total_ecart_secondes) })
                : bilan.total_ecart_secondes < 0
                  ? t("entrainement.syntheseAvance", { duree: formaterDuree(-bilan.total_ecart_secondes) })
                  : t("entrainement.synthesePile")}
            </p>
            {sectionsADepasser.length > 0 && (
              <p className="text-warmgray">
                {t("entrainement.aRaccourcir", { liste: sectionsADepasser.map((s) => s.point).join(" ; ") })}
              </p>
            )}
            {nonTraitees.length > 0 && (
              <p className="text-warmgray">
                {t("entrainement.nonTraitees", { liste: nonTraitees.map((s) => s.point).join(" ; ") })}
              </p>
            )}
          </div>
        </div>
      )}

      {seances.length >= 2 && phase !== "en_cours" && !enregistrement && (
        <div className="space-y-2">
          <h2 className="font-serif text-h4 font-semibold text-gold-500">{t("entrainement.historiqueTitre")}</h2>
          <div className="overflow-x-auto rounded-md border border-gold-600/20">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-gold-600/20 bg-surface-2 text-left text-micro uppercase tracking-wide text-warmgray">
                  <th className="px-4 py-3 font-medium">{t("entrainement.colDate")}</th>
                  <th className="px-4 py-3 font-medium">{t("entrainement.colAlloue")}</th>
                  <th className="px-4 py-3 font-medium">{t("entrainement.colReel")}</th>
                  <th className="px-4 py-3 font-medium">{t("entrainement.colEcart")}</th>
                  <th className="px-4 py-3 font-medium">{t("entrainement.colProgres")}</th>
                </tr>
              </thead>
              <tbody>
                {seances.map((seance) => (
                  <tr key={seance.id} className="border-b border-gold-600/10 last:border-0">
                    <td className="whitespace-nowrap px-4 py-3 text-ivory">
                      {new Date(seance.date).toLocaleString(locale, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-warmgray">{formaterChrono(seance.alloueSecondes)}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-warmgray">{formaterChrono(seance.reelSecondes)}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-warmgray">{formaterDuree(seance.ecartSecondes)}</td>
                    <td className="px-4 py-3 text-xs">
                      {seance.progresSecondes === null ? (
                        <span className="text-muted">—</span>
                      ) : seance.progresSecondes > 0 ? (
                        <span className="text-risk-low">▲ {t("entrainement.plusProche", { duree: formaterDuree(seance.progresSecondes) })}</span>
                      ) : seance.progresSecondes < 0 ? (
                        <span className="text-risk-high">▼ {t("entrainement.plusLoin", { duree: formaterDuree(-seance.progresSecondes) })}</span>
                      ) : (
                        <span className="text-muted">{t("entrainement.identique")}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
