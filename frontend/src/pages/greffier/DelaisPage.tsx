/**
 * DelaisPage — /greffier/delais. Suivi des délais de procédure du dossier
 * actif : le greffier choisit le type de délai et la date du point de
 * départ, le backend calcule l'échéance de façon déterministe (voir
 * backend/app/delais.py -- aucun appel IA, une date limite doit être
 * vérifiable). Le calcul est persisté dans documents_generes
 * (feature="delais") et rechargé au montage, comme la chronologie.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, greffier as greffierApi, downloadBlob } from "@/api";
import type { DelaiCalcule, DelaiDemande, DelaisResultat } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useDernierDocumentGenere } from "@/hooks/useDernierDocumentGenere";
import { classeUrgence, joursRestants, versDateLocale } from "@/config/echeances";
import Button from "@/components/Button";
import ConfirmerModal from "@/components/ConfirmerModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

export default function DelaisPage() {
  const { t, i18n } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const locale = i18n.language === "en" ? "en-GB" : "fr-FR";
  const formaterDate = (iso: string) =>
    versDateLocale(iso).toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  const [type, setType] = useState("");
  const [dateDepart, setDateDepart] = useState("");
  const [precision, setPrecision] = useState("");
  const [brouillons, setBrouillons] = useState<DelaiDemande[]>([]);
  const [exportEnCours, setExportEnCours] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);

  const { data: catalogue } = useAsync(() => greffierApi.catalogueDelais(), [], true);
  const { data, loading, error, executer, definirDonnees, reinitialiser } = useLazyAction((delais: DelaiDemande[]) =>
    greffierApi.calculerDelais(dossierActif!.id, delais)
  );
  const { document: dernierDocument, loading: dernierDocumentLoading } = useDernierDocumentGenere(dossierActif?.id, "delais");

  // Relit le dernier calcul persisté (simple GET, jamais un nouveau calcul)
  // et repré-remplit la liste éditable pour pouvoir y ajouter un délai.
  useEffect(() => {
    if (!dernierDocument || data) return;
    const contenu = dernierDocument.contenu as unknown as DelaisResultat;
    definirDonnees({ ...contenu, document_id: dernierDocument.id, statut: dernierDocument.statut });
    setBrouillons(contenu.delais.map((d) => ({ type: d.type, date_depart: d.date_depart, libelle: d.precision })));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dernierDocument]);

  const libelleType = (code: string) => catalogue?.find((c) => c.code === code)?.libelle ?? code;
  const typeChoisi = catalogue?.find((c) => c.code === type);

  const ajouter = () => {
    if (!type || !dateDepart) return;
    setBrouillons((liste) => [...liste, { type, date_depart: dateDepart, libelle: precision.trim() }]);
    setDateDepart("");
    setPrecision("");
  };

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await greffierApi.exporterDelais(dossierActif.id, data);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_delais.docx`);
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
      setBrouillons([]);
      setConfirmationSuppression(false);
      pousserToast("success", t("arsenal.resultatSupprime"));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurSuppression"));
    } finally {
      setSuppressionEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("delais.emptyTitre")} description={t("delais.emptyDescription")} />;
  }

  const delaisTries: DelaiCalcule[] = data ? [...data.delais].sort((a, b) => a.date_echeance.localeCompare(b.date_echeance)) : [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{t("nav.espace.greffier")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.greffier.delais")}</h1>
          <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
        </div>
        {data && (
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
            {data.document_id && (
              <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
            )}
          </div>
        )}
      </div>

      <p className="text-sm text-warmgray">{t("delais.sousTitre")}</p>

      <div className="card space-y-4 p-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label htmlFor="delai-type" className="mb-1 block text-micro font-medium uppercase tracking-wide text-warmgray">
              {t("delais.typeLabel")}
            </label>
            <select id="delai-type" className="input" value={type} onChange={(e) => setType(e.target.value)}>
              <option value="">{t("delais.typePlaceholder")}</option>
              {catalogue?.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.libelle} — {c.duree} ({c.reference})
                </option>
              ))}
            </select>
            {typeChoisi && (
              <p className="mt-1 text-xs text-muted">
                {t("delais.pointDeDepart")} : {typeChoisi.point_de_depart}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="delai-date" className="mb-1 block text-micro font-medium uppercase tracking-wide text-warmgray">
              {t("delais.dateDepartLabel")}
            </label>
            <input id="delai-date" type="date" className="input" value={dateDepart} onChange={(e) => setDateDepart(e.target.value)} />
          </div>
          <div>
            <label htmlFor="delai-precision" className="mb-1 block text-micro font-medium uppercase tracking-wide text-warmgray">
              {t("delais.precisionLabel")}
            </label>
            <input
              id="delai-precision"
              className="input"
              placeholder={t("delais.precisionPlaceholder")}
              maxLength={200}
              value={precision}
              onChange={(e) => setPrecision(e.target.value)}
            />
          </div>
        </div>
        <Button variant="secondary" disabled={!type || !dateDepart} onClick={ajouter}>
          ＋ {t("delais.ajouter")}
        </Button>

        {brouillons.length > 0 && (
          <ul className="space-y-2 border-t border-gold-600/20 pt-4">
            {brouillons.map((b, i) => (
              <li key={i} className="flex items-center justify-between gap-3 text-sm text-ivory">
                <span className="min-w-0 truncate">
                  {libelleType(b.type)} — {b.date_depart}
                  {b.libelle ? ` (${b.libelle})` : ""}
                </span>
                <button
                  onClick={() => setBrouillons((liste) => liste.filter((_, j) => j !== i))}
                  className="shrink-0 text-xs text-muted hover:text-risk-high"
                >
                  ✕ {t("coherence.retirer")}
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="flex justify-end">
          <Button variant="primary" loading={loading} disabled={brouillons.length === 0} onClick={() => void executer(brouillons)}>
            {data ? `↻ ${t("delais.recalculer")}` : t("delais.calculer")}
          </Button>
        </div>
      </div>

      {(loading || dernierDocumentLoading) && <SkeletonList count={2} />}

      {!loading && !dernierDocumentLoading && error && <ErrorState message={error} onRetry={() => void executer(brouillons)} />}

      {!loading && !dernierDocumentLoading && !error && data && (
        <div className="space-y-4">
          {delaisTries.map((d, i) => {
            const jours = joursRestants(d.date_echeance);
            return (
              <div key={i} className="card space-y-2 p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-serif text-h4 font-semibold text-ivory">{d.libelle}</p>
                    {d.precision && <p className="text-xs text-muted">{d.precision}</p>}
                  </div>
                  <span className={classeUrgence(jours)}>
                    {jours < 0 ? t("delais.depasse", { count: -jours }) : t("delais.joursRestants", { count: jours })}
                  </span>
                </div>
                <p className="font-mono text-sm font-semibold text-amethyst-400">
                  {t("delais.echeance")} : {formaterDate(d.date_echeance)}
                </p>
                {d.proroge && (
                  <p className="text-xs text-warmgray">{t("delais.prorogee", { date: formaterDate(d.echeance_brute) })}</p>
                )}
                <p className="text-xs text-muted">
                  {d.reference} — {d.duree} — {d.point_de_depart} : {formaterDate(d.date_depart)}
                </p>
              </div>
            );
          })}
          <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-4 text-xs text-ivory">
            ⚠ {t("delais.avertissement")}
          </div>
        </div>
      )}

      {!loading && !dernierDocumentLoading && !error && !data && (
        <EmptyState titre={t("delais.pretTitre")} description={t("delais.pretDescription")} />
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
