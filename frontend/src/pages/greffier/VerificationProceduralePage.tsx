/**
 * VerificationProceduralePage — /greffier/verification-procedurale ET
 * /arsenal/verification-procedurale (voir router.tsx : les deux chemins
 * pointent vers ce même composant). Le prompt système a été neutralisé
 * côté backend pour servir aussi bien l'avocat que le greffier ("aide un
 * professionnel du droit, avocat ou greffier" -- voir analyse.py) : un
 * avocat en a tout autant besoin avant de déposer un acte ou plaider.
 *
 * Échéances avec un statut coloré (À venir / Proche / Possiblement
 * dépassée / Date incertaine -- voir VERIFICATION_PROCEDURALE_SYSTEM_PROMPT),
 * actes potentiellement manquants (le plus actionnable, en rouge), points
 * d'attention (plus doux, en doré -- même convention que PlanTimeline).
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

// Valeurs fixes renvoyees par le backend (VERIFICATION_PROCEDURALE_SYSTEM_PROMPT)
// -- toujours ces tokens francais quelle que soit la langue de l'interface,
// meme principe que niveauRisque/niveauConfiance (voir RiskBadge.tsx).
const CLASSE_STATUT: Record<string, string> = {
  "À venir": "badge-risk-low",
  Proche: "badge-risk-medium",
  "Possiblement dépassée": "badge-risk-high",
};
const CLASSE_STATUT_DEFAUT = "badge border-muted/30 bg-surface-2 text-warmgray";

export default function VerificationProceduralePage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [exportEnCours, setExportEnCours] = useState(false);
  const { data, loading, error, executer, definirDonnees } = useLazyAction(() => greffierApi.verificationProcedurale(dossierActif!.id));

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await greffierApi.exporterVerificationProcedurale(dossierActif.id, data);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_verification_procedurale.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("verifProcedurale.emptyTitre")} description={t("verifProcedurale.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{t("nav.arsenal.verification-procedurale")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("verifProcedurale.titre")}</h1>
          <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {data && (
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
          )}
          <Button variant="primary" loading={loading} onClick={() => void executer()}>
            {data ? `↻ ${t("verifProcedurale.relancer")}` : t("verifProcedurale.verifier")}
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-6">
          <div>
            <p className="mb-3 font-serif text-h3 font-semibold text-gold-500">{t("verifProcedurale.echeancesIdentifiees")}</p>
            {data.echeances_identifiees.length === 0 ? (
              <p className="text-sm text-muted">{t("verifProcedurale.aucuneEcheance")}</p>
            ) : (
              <div className="space-y-2.5">
                {data.echeances_identifiees.map((ech, i) => (
                  <div key={i} className="card flex flex-wrap items-center justify-between gap-3 p-4">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-ivory">{ech.echeance}</p>
                      <p className="text-xs text-muted">{ech.date}</p>
                    </div>
                    <span className={CLASSE_STATUT[ech.statut] ?? CLASSE_STATUT_DEFAUT}>{t(`statutEcheance.${ech.statut}`, ech.statut)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {data.actes_potentiellement_manquants.length > 0 && (
            <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
              <p className="mb-2 text-sm font-semibold text-risk-high">⚠ {t("verifProcedurale.actesManquants")}</p>
              <ul className="space-y-1.5">
                {data.actes_potentiellement_manquants.map((a, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ivory">
                    <span className="text-risk-high">•</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.points_attention.length > 0 && (
            <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-5">
              <p className="mb-2 text-sm font-semibold text-gold-500">{t("planTimeline.pointsAttention")}</p>
              <ul className="space-y-1.5">
                {data.points_attention.map((p, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ivory">
                    <span className="text-gold-500">•</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <ChatContextuelPanel
            feature="verification_procedurale"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            placeholder={t("verifProcedurale.chatPlaceholder")}
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre={t("verifProcedurale.pretTitre")}
          description={t("verifProcedurale.pretDescription")}
        />
      )}
    </div>
  );
}
