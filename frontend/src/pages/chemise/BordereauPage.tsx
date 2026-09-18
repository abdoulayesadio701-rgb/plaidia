/**
 * BordereauPage — /chemise/bordereau (Avocat) et /greffier/bordereau
 * (Greffier) : même page, mêmes données. Liste numérotée des pièces du
 * dossier actif, enregistrée côté serveur dans une seule entrée
 * documents_generes (feature="bordereau") mise à jour sur place, exportable
 * en Word (tableau à annexer). Aucun appel IA : c'est une saisie.
 *
 * L'ordre de la liste fait le numéro : réordonner ou supprimer une pièce
 * renumérote 1..n. Le numéro reste modifiable à la main, tant qu'il n'y a
 * pas de doublon (l'enregistrement est alors bloqué).
 */

import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, bordereau as bordereauApi, downloadBlob } from "@/api";
import type { PieceBordereau } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import Button from "@/components/Button";
import ConfirmerModal from "@/components/ConfirmerModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

const PRODUITE_PAR = ["Demandeur", "Défendeur", "Tiers"];

function renumeroter(pieces: PieceBordereau[]): PieceBordereau[] {
  return pieces.map((p, i) => ({ ...p, numero: i + 1 }));
}

export default function BordereauPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const estGreffier = location.pathname.startsWith("/app/greffier");

  const [pieces, setPieces] = useState<PieceBordereau[]>([]);
  const [enregistre, setEnregistre] = useState("[]");
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [enregistrementEnCours, setEnregistrementEnCours] = useState(false);
  const [exportEnCours, setExportEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);

  const { data, loading, error, reload } = useAsync(
    () => bordereauApi.lireBordereau(dossierActif!.id),
    [dossierActif?.id],
    dossierActif !== null
  );
  const { data: sources } = useAsync(() => bordereauApi.sourcesImportees(dossierActif!.id), [dossierActif?.id], dossierActif !== null);

  useEffect(() => {
    if (!data) return;
    setPieces(data.pieces);
    setEnregistre(JSON.stringify(data.pieces));
    setDocumentId(data.document_id);
  }, [data]);

  const modifie = JSON.stringify(pieces) !== enregistre;
  const numeros = pieces.map((p) => p.numero);
  const doublons = new Set(numeros).size !== numeros.length;
  const sansIntitule = pieces.some((p) => !p.intitule.trim());
  const sourcesDisponibles = (sources ?? []).filter((nom) => !pieces.some((p) => p.intitule === nom));

  const maj = (i: number, patch: Partial<PieceBordereau>) =>
    setPieces((liste) => liste.map((p, j) => (j === i ? { ...p, ...patch } : p)));

  const ajouter = (intitule = "") =>
    setPieces((liste) => [
      ...liste,
      { numero: Math.max(0, ...liste.map((p) => p.numero)) + 1, intitule, date: "", produite_par: "", observation: "" },
    ]);

  const retirer = (i: number) => setPieces((liste) => renumeroter(liste.filter((_, j) => j !== i)));

  const deplacer = (i: number, sens: -1 | 1) =>
    setPieces((liste) => {
      const cible = i + sens;
      if (cible < 0 || cible >= liste.length) return liste;
      const copie = [...liste];
      [copie[i], copie[cible]] = [copie[cible], copie[i]];
      return renumeroter(copie);
    });

  const enregistrer = async () => {
    if (!dossierActif) return;
    setEnregistrementEnCours(true);
    try {
      const resultat = await bordereauApi.enregistrerBordereau(
        dossierActif.id,
        pieces.map((p) => ({ ...p, intitule: p.intitule.trim() }))
      );
      setPieces(resultat.pieces);
      setEnregistre(JSON.stringify(resultat.pieces));
      setDocumentId(resultat.document_id);
      pousserToast("success", t("bordereau.enregistre"));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("bordereau.erreurEnregistrement"));
    } finally {
      setEnregistrementEnCours(false);
    }
  };

  const supprimerBordereau = async () => {
    if (documentId === null) return;
    setSuppressionEnCours(true);
    try {
      await analyseApi.supprimerDocumentGenere(documentId);
      setConfirmationSuppression(false);
      setPieces([]);
      setEnregistre("[]");
      setDocumentId(null);
      pousserToast("success", t("arsenal.resultatSupprime"));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurSuppression"));
    } finally {
      setSuppressionEnCours(false);
    }
  };

  const exporter = async () => {
    if (!dossierActif) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await bordereauApi.exporterBordereau(dossierActif.id);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_bordereau.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("bordereau.emptyTitre")} description={t("bordereau.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{estGreffier ? t("nav.espace.greffier") : t("nav.sections.chemise")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("bordereau.titre")}</h1>
          <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {modifie && <span className="text-xs text-risk-medium">{t("bordereau.nonEnregistre")}</span>}
          <Button variant="secondary" loading={exportEnCours} disabled={modifie || enregistre === "[]"} onClick={() => void exporter()}>
            ⬇ {t("arsenal.exporterWord")}
          </Button>
          {documentId !== null && (
            <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>
              🗑 {t("bordereau.supprimerTout")}
            </Button>
          )}
          <Button
            variant="primary"
            loading={enregistrementEnCours}
            disabled={!modifie || doublons || sansIntitule}
            onClick={() => void enregistrer()}
          >
            {t("bordereau.enregistrer")}
          </Button>
        </div>
      </div>

      <p className="text-sm text-warmgray">{t("bordereau.sousTitre")}</p>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && (
        <div className="space-y-4">
          {pieces.length === 0 && (
            <EmptyState titre={t("bordereau.videTitre")} description={t("bordereau.videDescription")} />
          )}

          {pieces.map((p, i) => (
            <div key={i} className="card space-y-3 p-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-[5rem_1fr_10rem_11rem]">
                <div>
                  <label htmlFor={`piece-numero-${i}`} className="mb-1 block text-micro font-medium uppercase tracking-wide text-warmgray">
                    {t("bordereau.numero")}
                  </label>
                  <input
                    id={`piece-numero-${i}`}
                    type="number"
                    min={1}
                    className="input"
                    value={p.numero}
                    onChange={(e) => maj(i, { numero: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label htmlFor={`piece-intitule-${i}`} className="mb-1 block text-micro font-medium uppercase tracking-wide text-warmgray">
                    {t("bordereau.intitule")}
                  </label>
                  <input
                    id={`piece-intitule-${i}`}
                    className="input"
                    maxLength={300}
                    value={p.intitule}
                    onChange={(e) => maj(i, { intitule: e.target.value })}
                  />
                </div>
                <div>
                  <label htmlFor={`piece-date-${i}`} className="mb-1 block text-micro font-medium uppercase tracking-wide text-warmgray">
                    {t("bordereau.date")}
                  </label>
                  <input id={`piece-date-${i}`} type="date" className="input" value={p.date} onChange={(e) => maj(i, { date: e.target.value })} />
                </div>
                <div>
                  <label htmlFor={`piece-produite-${i}`} className="mb-1 block text-micro font-medium uppercase tracking-wide text-warmgray">
                    {t("bordereau.produitePar")}
                  </label>
                  <input
                    id={`piece-produite-${i}`}
                    className="input"
                    list="bordereau-produite-par"
                    maxLength={100}
                    value={p.produite_par}
                    onChange={(e) => maj(i, { produite_par: e.target.value })}
                  />
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <input
                  className="input min-w-0 flex-1"
                  aria-label={t("bordereau.observation")}
                  placeholder={t("bordereau.observation")}
                  maxLength={300}
                  value={p.observation}
                  onChange={(e) => maj(i, { observation: e.target.value })}
                />
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    onClick={() => deplacer(i, -1)}
                    disabled={i === 0}
                    aria-label={t("bordereau.monter")}
                    className="rounded-md px-2 py-1 text-sm text-warmgray hover:text-ivory disabled:opacity-30"
                  >
                    ↑
                  </button>
                  <button
                    onClick={() => deplacer(i, 1)}
                    disabled={i === pieces.length - 1}
                    aria-label={t("bordereau.descendre")}
                    className="rounded-md px-2 py-1 text-sm text-warmgray hover:text-ivory disabled:opacity-30"
                  >
                    ↓
                  </button>
                  <button
                    onClick={() => retirer(i)}
                    aria-label={t("bordereau.retirer")}
                    className="rounded-md px-2 py-1 text-xs text-muted hover:text-risk-high"
                  >
                    ✕ {t("bordereau.retirer")}
                  </button>
                </div>
              </div>
            </div>
          ))}

          <datalist id="bordereau-produite-par">
            {PRODUITE_PAR.map((valeur) => (
              <option key={valeur} value={valeur} />
            ))}
          </datalist>

          {doublons && <p className="text-xs text-risk-high">{t("bordereau.numeroEnDouble")}</p>}

          <div className="flex flex-wrap items-center gap-3">
            <Button variant="secondary" onClick={() => ajouter()}>
              ＋ {t("bordereau.ajouter")}
            </Button>
            {sourcesDisponibles.length > 0 && (
              <select
                className="input w-auto"
                aria-label={t("bordereau.depuisImport")}
                value=""
                onChange={(e) => e.target.value && ajouter(e.target.value)}
              >
                <option value="">{t("bordereau.depuisImport")}</option>
                {sourcesDisponibles.map((nom) => (
                  <option key={nom} value={nom}>
                    {nom}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      )}

      {confirmationSuppression && (
        <ConfirmerModal
          titre={t("bordereau.supprimerToutTitre")}
          description={t("bordereau.supprimerToutDescription")}
          texteBouton={t("commun.supprimer")}
          enCours={suppressionEnCours}
          onFermer={() => setConfirmationSuppression(false)}
          onConfirmer={supprimerBordereau}
        />
      )}
    </div>
  );
}
