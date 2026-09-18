/**
 * TableauDeBord — synthèse du dossier actif sur la page d'accueil :
 * prochaine échéance, pièces au bordereau, dernier entraînement, veille
 * juridique, documents récents. Une seule lecture réseau
 * (GET /api/dossiers/{id}/documents-generes) ; l'agrégation est faite par
 * synthetiser() (voir synthese.ts). Une carte n'apparaît que si elle a une
 * donnée à montrer.
 */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { dossiers as dossiersApi } from "@/api";
import { useAlertesArticlesDossier } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { cheminDocument } from "@/config/cheminsDocuments";
import { formaterDuree } from "@/config/durees";
import { classeUrgence, versDateLocale } from "@/config/echeances";
import { SkeletonList } from "@/components/Skeleton";
import { StatutDocumentBadge } from "@/components/StatutDocument";
import { synthetiser } from "./synthese";

const CLASSE_CARTE = "card block space-y-1.5 p-4 transition-colors hover:border-gold-500/40";
const CLASSE_TITRE = "text-micro font-medium uppercase tracking-wide text-amethyst-400";

export default function TableauDeBord({ dossierId }: { dossierId: number }) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === "en" ? "en-GB" : "fr-FR";
  const alertes = useAlertesArticlesDossier(dossierId);
  const { data: documents, loading, error } = useAsync(() => dossiersApi.listerDocumentsGeneres(dossierId), [dossierId], true);
  const synthese = useMemo(() => (documents ? synthetiser(documents) : null), [documents]);

  if (loading) return <SkeletonList count={2} />;
  if (error || !synthese) return <p className="text-xs text-muted">{t("dashboard.indisponible")}</p>;

  const { prochaineEcheance, echeancesDepassees, nombrePieces, dernierEntrainement, recents } = synthese;
  const aUneEcheance = prochaineEcheance !== null || echeancesDepassees > 0;
  const rienAMontrer = !aUneEcheance && nombrePieces === null && !dernierEntrainement && alertes.length === 0 && recents.length === 0;

  if (rienAMontrer) {
    return <p className="text-center text-sm text-muted">{t("dashboard.vide")}</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 text-left sm:grid-cols-2">
      {aUneEcheance && (
        <Link to="/app/greffier/delais" className={CLASSE_CARTE}>
          <p className={CLASSE_TITRE}>{t("dashboard.prochaineEcheance")}</p>
          {prochaineEcheance && (
            <>
              <p className="text-sm font-medium text-ivory">{prochaineEcheance.delai.libelle}</p>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-warmgray">
                  {versDateLocale(prochaineEcheance.delai.date_echeance).toLocaleDateString(locale, {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </span>
                <span className={classeUrgence(prochaineEcheance.jours)}>
                  {prochaineEcheance.jours === 0
                    ? t("dashboard.aujourdhui")
                    : t("delais.joursRestants", { count: prochaineEcheance.jours })}
                </span>
              </div>
            </>
          )}
          {echeancesDepassees > 0 && (
            <p className="text-sm font-medium text-risk-high">{t("dashboard.echeancesDepassees", { count: echeancesDepassees })}</p>
          )}
        </Link>
      )}

      {nombrePieces !== null && (
        <Link to="/app/chemise/bordereau" className={CLASSE_CARTE}>
          <p className={CLASSE_TITRE}>{t("dashboard.bordereau")}</p>
          <p className="text-sm text-ivory">{t("dashboard.pieces", { count: nombrePieces })}</p>
        </Link>
      )}

      {dernierEntrainement && (
        <Link to="/app/arsenal/entrainement" className={CLASSE_CARTE}>
          <p className={CLASSE_TITRE}>{t("dashboard.entrainement")}</p>
          <p className="text-sm text-ivory">
            {t("dashboard.entrainementDetail", {
              reel: formaterDuree(dernierEntrainement.total_reel_secondes),
              alloue: formaterDuree(dernierEntrainement.total_alloue_secondes),
            })}
          </p>
        </Link>
      )}

      {alertes.length > 0 && (
        <Link to="/app/chemise/historique" className={`${CLASSE_CARTE} border-risk-high/40`}>
          <p className={CLASSE_TITRE}>{t("dashboard.veille")}</p>
          <p className="text-sm font-medium text-risk-high">⚠ {t("dashboard.alertes", { count: alertes.length })}</p>
        </Link>
      )}

      {recents.length > 0 && (
        <div className="card space-y-2 p-4 sm:col-span-2">
          <p className={CLASSE_TITRE}>{t("dashboard.recents")}</p>
          <ul className="space-y-1">
            {recents.map((document) => (
              <li key={document.id}>
                <Link
                  to={`/app/${cheminDocument(document.feature)}?document_id=${document.id}`}
                  className="flex items-center justify-between gap-3 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-surface-2"
                >
                  <span className="min-w-0 truncate text-ivory">{document.titre}</span>
                  <span className="flex shrink-0 items-center gap-2">
                    <StatutDocumentBadge statut={document.statut} />
                    <span className="text-xs text-muted">
                      {new Date(document.date_modification).toLocaleDateString(locale, { day: "2-digit", month: "short" })}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
