/**
 * ClassementPage — /greffier/classement. Classe un document selon sa
 * nature (assignation, jugement, ordonnance, conclusions, pièce, requête,
 * citation, procès-verbal, autre), avec une jauge de confiance et une
 * justification. Collage ou import de fichier (voir useImportTexte),
 * indépendant de tout dossier (requiresDossier: false) -- un dossier actif
 * reste optionnel, seulement pour aussi ajouter le texte à ses faits.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { greffier as greffierApi } from "@/api";
import { useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useImportTexte } from "@/hooks/useImportTexte";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import ChoixImportModal from "@/components/ChoixImportModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import RichOutput from "@/components/RichOutput";
import JaugeConfiance from "@/components/JaugeConfiance";
import { SkeletonList } from "@/components/Skeleton";

export default function ClassementPage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const [texte, setTexte] = useState("");

  const { data, loading, error, executer } = useLazyAction((t: string) => greffierApi.classement(t));
  // Page indépendante de tout dossier (requiresDossier: false) -- voir
  // useImportTexte : dossier actif optionnel, extraireFichier sinon.
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: dossierActif?.id ?? null,
    getTexteActuel: () => texte,
    onTexteExtrait: setTexte,
  });

  const lancer = () => void executer(texte);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.espace.greffier")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.greffier.classement")}</h1>
        <p className="mt-2 text-sm text-warmgray">{t("classement.sousTitre")}</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          {...dragProps}
          className={`input min-h-[220px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
          placeholder={t("classement.placeholder")}
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
              {dossierActif
                ? t("analyseStyle.texteAjouteAuxFaits", { nom: dossierActif.nom })
                : t("arsenal.formatsAcceptes")}
            </span>
          </div>
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={lancer}>
            {t("classement.classer")}
          </Button>
        </div>
      </div>

      {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

      {loading && <SkeletonList count={1} />}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
        <div className="card space-y-5 p-6">
          <div>
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{t("classement.natureDocument")}</p>
            <p className="mt-1 font-serif text-h3 font-semibold capitalize text-gold-500">{t(`natureDocument.${data.nature}`, data.nature)}</p>
          </div>
          <JaugeConfiance niveau={data.confiance} />
          <div>
            <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">{t("classement.justification")}</p>
            <RichOutput texte={data.justification} prose={false} className="text-sm" />
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre={t("classement.pretTitre")} description={t("classement.pretDescription")} />
      )}
    </div>
  );
}
