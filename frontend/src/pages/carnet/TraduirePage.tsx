/**
 * TraduirePage — /carnet/traduire. Ne nécessite pas de dossier actif (voir
 * navigation.ts, requiresDossier: false) — traduction juridique français ↔
 * anglais d'un texte collé, indépendante d'un dossier précis. Utilise Claude
 * directement (voir analyse.py::traduire_texte) plutôt qu'un moteur de
 * traduction générique, pour préserver la terminologie juridique précise.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, downloadBlob } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useImportTexte } from "@/hooks/useImportTexte";
import { useValeurPersistante, useResultatPersistant, effacerBrouillons } from "@/hooks/useBrouillonPersistant";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import ChoixImportModal from "@/components/ChoixImportModal";
import ConfirmerModal from "@/components/ConfirmerModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import RichOutput from "@/components/RichOutput";
import { SkeletonBlock } from "@/components/Skeleton";

const CLE_TEXTE = "plaidia:traduire:texte";
const CLE_RESULTAT = "plaidia:traduire:resultat";

export default function TraduirePage() {
  const { t } = useTranslation();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const LABEL_LANGUE: Record<string, string> = { fr: t("traduire.francais"), en: t("traduire.anglais") };
  const [texte, setTexte] = useValeurPersistante(CLE_TEXTE, "");
  const [exportEnCours, setExportEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);
  const { data, loading, error, executer, definirDonnees, reinitialiser } = useLazyAction((t: string) => analyseApi.traduireTexte(t));
  // Page indépendante de tout dossier (requiresDossier: false) -- pas de
  // documents_generes côté serveur possible, persistance locale à la place
  // (voir useBrouillonPersistant) : le brouillon survit à une navigation ou
  // un refresh, propre à cet appareil.
  useResultatPersistant(CLE_RESULTAT, data, definirDonnees);
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: null,
    getTexteActuel: () => texte,
    onTexteExtrait: setTexte,
  });

  const supprimer = () => {
    reinitialiser();
    setTexte("");
    effacerBrouillons(CLE_TEXTE, CLE_RESULTAT);
    setConfirmationSuppression(false);
  };

  const copier = async () => {
    if (!data?.texte_traduit) return;
    try {
      await navigator.clipboard.writeText(data.texte_traduit);
    } catch {
      // Silencieux : le texte reste sélectionnable/copiable à la main dans la carte ci-dessous.
    }
  };

  const exporter = async () => {
    if (!data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await analyseApi.exporterTraduction(data);
      downloadBlob(blob, filename ?? "traduction.docx");
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.carnet")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.carnet.traduire")}</h1>
        <p className="mt-2 text-sm text-warmgray">
          {t("traduire.sousTitre")}
        </p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          {...dragProps}
          className={`input min-h-[200px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
          placeholder={t("traduire.placeholder")}
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          disabled={loading || enImport}
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <FileDropZone
              variante="compact"
              extensions={EXTENSIONS_DOCUMENT}
              multiple
              loading={enImport}
              disabled={loading}
              onFichiers={importerFichiers}
            />
            <span className="text-xs text-muted">{t("arsenal.formatsAcceptes")}</span>
          </div>
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={() => void executer(texte)}>
            {t("traduire.traduire")}
          </Button>
        </div>
      </div>

      {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

      {loading && (
        <div className="card space-y-2.5 p-6">
          <SkeletonBlock className="h-4 w-1/3" />
          <SkeletonBlock className="h-4 w-full" />
          <SkeletonBlock className="h-4 w-5/6" />
          <SkeletonBlock className="h-4 w-2/3" />
        </div>
      )}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer(texte)} />}

      {!loading && !error && data && (
        <div className="card space-y-4 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">
              {t("traduire.detecteTraduit", {
                detectee: LABEL_LANGUE[data.langue_detectee] ?? data.langue_detectee,
                cible: LABEL_LANGUE[data.langue_cible] ?? data.langue_cible,
              })}
            </p>
            <div className="flex items-center gap-3">
              <button onClick={() => void copier()} className="text-xs text-amethyst-400 hover:underline">
                {t("traduire.copierTraduction")}
              </button>
              <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
                ⬇ {t("arsenal.exporterWord")}
              </Button>
              <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
            </div>
          </div>
          <RichOutput texte={data.texte_traduit} />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre={t("traduire.pretTitre")} description={t("traduire.pretDescription")} />
      )}

      {confirmationSuppression && (
        <ConfirmerModal
          titre={t("arsenal.confirmerSuppressionTitre")}
          description={t("arsenal.confirmerSuppressionDescription")}
          texteBouton={t("commun.supprimer")}
          onFermer={() => setConfirmationSuppression(false)}
          onConfirmer={supprimer}
        />
      )}
    </div>
  );
}
