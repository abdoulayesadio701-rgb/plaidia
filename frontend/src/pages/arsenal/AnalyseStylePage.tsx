/**
 * AnalyseStylePage — /arsenal/style. Ne nécessite pas de dossier actif
 * (voir navigation.ts, requiresDossier: false) — analyse rhétorique d'un
 * texte collé, indépendante d'un dossier précis.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { analyse as analyseApi, downloadBlob } from "@/api";
import type { StyleResultat } from "@/api";
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
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

type CleSection = "langage_de_couverture" | "affirmations_absolues" | "voix_passive_suspecte" | "ruptures_registre";

const SECTIONS: { key: CleSection; cleLabel: string; icone: string }[] = [
  { key: "langage_de_couverture", cleLabel: "analyseStyle.langageCouverture", icone: "🗣️" },
  { key: "affirmations_absolues", cleLabel: "analyseStyle.affirmationsAbsolues", icone: "⚠️" },
  { key: "voix_passive_suspecte", cleLabel: "analyseStyle.voixPassiveSuspecte", icone: "👤" },
  { key: "ruptures_registre", cleLabel: "analyseStyle.rupturesRegistre", icone: "📉" },
];

const CLE_TEXTE = "plaidia:style:texte";
const CLE_RESULTAT = "plaidia:style:resultat";

export default function AnalyseStylePage() {
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [texte, setTexte] = useValeurPersistante(CLE_TEXTE, "");
  const [exportEnCours, setExportEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);

  const { data, loading, error, executer, definirDonnees, reinitialiser } = useLazyAction((t: string) => analyseApi.analyserStyle(t));
  // Page indépendante de tout dossier (requiresDossier: false) -- pas de
  // documents_generes côté serveur possible, persistance locale à la place
  // (voir useBrouillonPersistant).
  useResultatPersistant(CLE_RESULTAT, data, definirDonnees);

  const exporter = async () => {
    if (!data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await analyseApi.exporterStyle(data);
      downloadBlob(blob, filename ?? "analyse_style.docx");
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  const supprimer = () => {
    reinitialiser();
    setTexte("");
    effacerBrouillons(CLE_TEXTE, CLE_RESULTAT);
    setConfirmationSuppression(false);
  };
  // Page indépendante de tout dossier (requiresDossier: false) -- un dossier
  // actif reste optionnel : quand il y en a un, le texte extrait est aussi
  // ajouté à ses faits (importerDocument) ; sinon, extraction seule
  // (extraireFichier), sans rien écrire en base -- voir useImportTexte.
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: dossierActif?.id ?? null,
    getTexteActuel: () => texte,
    onTexteExtrait: setTexte,
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.arsenal")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.arsenal.style")}</h1>
        <p className="mt-2 text-sm text-warmgray">{t("analyseStyle.sousTitre")}</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          {...dragProps}
          className={`input min-h-[220px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
          placeholder={t("analyseStyle.placeholder")}
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
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={() => void executer(texte)}>
            {t("analyseStyle.analyser")}
          </Button>
        </div>
      </div>

      {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

      {loading && <SkeletonList count={4} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer(texte)} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="flex justify-end gap-2">
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
            <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
          </div>
          <ResultatStyle data={data} t={t} />
          <ChatContextuelPanel
            feature="style"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            placeholder={t("analyseStyle.chatPlaceholder")}
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre={t("analyserConclusions.pretTitre")}
          description={t("analyseStyle.pretDescription")}
        />
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

function ResultatStyle({ data, t }: { data: StyleResultat; t: TFunction }) {
  return (
    <div className="space-y-5">
      {SECTIONS.map((section) => {
        const elements = data[section.key];
        return (
          <div key={section.key} className="card p-6">
            <p className="mb-3 font-serif text-h4 font-semibold text-ivory">
              {section.icone} {t(section.cleLabel)}
            </p>
            {elements.length === 0 ? (
              <p className="text-sm text-muted">{t("analyseStyle.rienDetecte")}</p>
            ) : (
              <ul className="space-y-3">
                {elements.map((el, i) => (
                  <li key={i} className="border-l-2 border-gold-600/30 pl-3">
                    <p className="text-sm italic text-ivory">« {el.citation} »</p>
                    <RichOutput texte={el.commentaire} prose={false} className="mt-1 text-sm text-warmgray" />
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}

      {data.synthese_strategique && (
        <div className="card border-amethyst-400/30 p-6">
          <p className="mb-2 text-micro font-medium uppercase tracking-wide text-amethyst-400">💡 {t("analyseStyle.syntheseStrategique")}</p>
          <RichOutput texte={data.synthese_strategique} />
        </div>
      )}

      <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-4 text-sm text-gold-500">
        ⚡ {t("analyseStyle.avertissement")}
      </div>
    </div>
  );
}
