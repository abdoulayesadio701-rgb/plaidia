/**
 * PageAnalyseTexte — squelette commun des pages Greffier « un texte en
 * entrée, une analyse structurée en sortie » (réquisitoire, rapport
 * d'instruction) : collage ou import du texte, lancement, résultat rendu par
 * la page appelante, export Word, suppression avec confirmation.
 *
 * Indépendant de tout dossier : persistance locale du texte et du résultat
 * (voir useBrouillonPersistant), comme Extraction ou Classement.
 */

import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { downloadBlob } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
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
import { SkeletonList } from "@/components/Skeleton";

interface PageAnalyseTexteProps<T> {
  /** Préfixe des clés de stockage local : plaidia:<cle>:texte / :resultat. */
  cle: string;
  titre: string;
  sousTitre: string;
  placeholder: string;
  libelleLancer: string;
  pretTitre: string;
  pretDescription: string;
  nomFichierExport: string;
  lancer: (texte: string) => Promise<T>;
  exporter: (resultat: T) => Promise<{ blob: Blob; filename?: string }>;
  rendreResultat: (resultat: T) => ReactNode;
}

export default function PageAnalyseTexte<T>({
  cle,
  titre,
  sousTitre,
  placeholder,
  libelleLancer,
  pretTitre,
  pretDescription,
  nomFichierExport,
  lancer,
  exporter,
  rendreResultat,
}: PageAnalyseTexteProps<T>) {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const cleTexte = `plaidia:${cle}:texte`;
  const cleResultat = `plaidia:${cle}:resultat`;
  const [texte, setTexte] = useValeurPersistante(cleTexte, "");
  const [exportEnCours, setExportEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);

  const { data, loading, error, executer, definirDonnees, reinitialiser } = useLazyAction((contenu: string) => lancer(contenu));
  useResultatPersistant<T>(cleResultat, data, definirDonnees);
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: dossierActif?.id ?? null,
    getTexteActuel: () => texte,
    onTexteExtrait: setTexte,
  });

  const lancerAnalyse = () => void executer(texte);

  const telecharger = async () => {
    if (!data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await exporter(data);
      downloadBlob(blob, filename ?? nomFichierExport);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  const supprimer = () => {
    reinitialiser();
    setTexte("");
    effacerBrouillons(cleTexte, cleResultat);
    setConfirmationSuppression(false);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.espace.greffier")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{titre}</h1>
        <p className="mt-2 text-sm text-warmgray">{sousTitre}</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          {...dragProps}
          className={`input min-h-[220px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
          placeholder={placeholder}
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
            <span className="text-xs text-muted">
              {dossierActif ? t("analyseStyle.texteAjouteAuxFaits", { nom: dossierActif.nom }) : t("arsenal.formatsAcceptes")}
            </span>
          </div>
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={lancerAnalyse}>
            {libelleLancer}
          </Button>
        </div>
      </div>

      {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={lancerAnalyse} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="flex justify-end gap-2">
            <Button variant="secondary" loading={exportEnCours} onClick={() => void telecharger()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
            <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
          </div>
          {rendreResultat(data)}
        </div>
      )}

      {!loading && !error && !data && <EmptyState titre={pretTitre} description={pretDescription} />}

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
