/**
 * ConsulterJurisprudencePage — /grimoire/jurisprudence. Question libre sur
 * la jurisprudence applicable, recherchée dans la juridiction active
 * (Légifrance en direct, ou un corpus validé -- voir la section
 * « Paramètres juridiques » de /grimoire/corpus pour la changer).
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { jurisprudence as jurisprudenceApi } from "@/api";
import { analyse as analyseApi } from "@/api";
import type { ConsulterResultat, StatutDocument } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useImportTexte } from "@/hooks/useImportTexte";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import ChoixImportModal from "@/components/ChoixImportModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";
import VerificationPanel from "@/components/VerificationPanel";
import StatutDocumentMenu, { StatutDocumentBadge } from "@/components/StatutDocument";
import { useAsync } from "@/hooks/useAsync";

export default function ConsulterJurisprudencePage() {
  const { t } = useTranslation();
  const juridictionActive = useAppStore((s) => s.juridictionActive);
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [searchParams] = useSearchParams();
  const [question, setQuestion] = useState("");
  const [but, setBut] = useState("");
  const [statutEnCours, setStatutEnCours] = useState(false);
  const documentId = Number(searchParams.get("document_id"));
  const aDocument = Number.isInteger(documentId) && documentId > 0;

  const { data, loading, error, executer, definirDonnees } = useLazyAction((q: string, b: string) =>
    jurisprudenceApi.consulterJurisprudence(q, b, juridictionActive, dossierActif!.id)
  );
  const { data: document, loading: documentLoading, error: documentError } = useAsync(
    () => analyseApi.obtenirDocumentGenere(documentId),
    [documentId, dossierActif?.id],
    aDocument && dossierActif !== null
  );
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: dossierActif?.id ?? null,
    getTexteActuel: () => question,
    onTexteExtrait: setQuestion,
  });

  useEffect(() => {
    if (!document || document.feature !== "jurisprudence_consultation" || document.dossier_id !== dossierActif?.id) return;
    definirDonnees({ ...(document.contenu as unknown as ConsulterResultat), document_id: document.id, statut: document.statut });
    setQuestion(typeof document.parametres.question === "string" ? document.parametres.question : "");
    setBut(typeof document.parametres.but === "string" ? document.parametres.but : "");
  }, [document, dossierActif?.id, definirDonnees]);

  const changerStatut = async (statut: StatutDocument) => {
    if (!data?.document_id) return;
    setStatutEnCours(true);
    try {
      await analyseApi.changerStatutDocument(data.document_id, statut);
      definirDonnees({ ...data, statut });
      pousserToast("success", t("statutDocument.changePousse", { statut: t(`statutDocument.${statut}`, statut) }));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurChangementStatut"));
    } finally {
      setStatutEnCours(false);
    }
  };

  const lancer = () => void executer(question, but);

  if (!dossierActif) {
    return <EmptyState titre={t("consulterJurisprudence.emptyTitre")} description={t("consulterJurisprudence.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.grimoire")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.grimoire.jurisprudence")}</h1>
        <p className="mt-2 flex items-center gap-2 text-sm text-warmgray">
          {t("topBar.juridictionActiveAria")} :
          <span className="badge border-amethyst-400/40 bg-amethyst-400/10 text-amethyst-400">{juridictionActive}</span>
        </p>
      </div>

      <div className="card space-y-4 p-6">
        <div>
          <label htmlFor="cj-question" className="mb-1.5 block text-sm text-warmgray">
            {t("consulterJurisprudence.situationLabel")}
          </label>
          <textarea
            {...dragProps}
            id="cj-question"
            className={`input min-h-[140px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
            placeholder={t("consulterJurisprudence.situationPlaceholder")}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading || enImport}
          />
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <FileDropZone
              variante="compact"
              extensions={EXTENSIONS_DOCUMENT}
              multiple
              loading={enImport}
              disabled={loading}
              onFichiers={importerFichiers}
            />
            <span className="text-xs text-muted">{t("analyseStyle.texteAjouteAuxFaits", { nom: dossierActif.nom })}</span>
          </div>
        </div>

        {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}
        <div>
          <label htmlFor="cj-but" className="mb-1.5 block text-sm text-warmgray">
            {t("consulterJurisprudence.butLabel")}
          </label>
          <input
            id="cj-but"
            className="input"
            placeholder={t("consulterJurisprudence.butPlaceholder")}
            value={but}
            onChange={(e) => setBut(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} disabled={!question.trim()} onClick={lancer}>
            {t("consulterJurisprudence.consulter")}
          </Button>
        </div>
      </div>

      {(loading || documentLoading) && <SkeletonList count={2} />}

      {!loading && !documentLoading && (error || documentError) && <ErrorState message={error ?? documentError ?? t("arsenal.erreurChargement")} onRetry={lancer} />}

      {!loading && !documentLoading && !error && !documentError && data && (
        <div className="space-y-5">
          <div className="flex items-center justify-between gap-3"><span className="text-sm text-warmgray">{t("consulterJurisprudence.consultationSauvegardee")}</span><div className="flex items-center gap-2"><StatutDocumentBadge statut={data.statut ?? "Brouillon"} /><StatutDocumentMenu statut={data.statut ?? "Brouillon"} loading={statutEnCours} onChange={changerStatut} /></div></div>
          <div className="card space-y-2 border-amethyst-400/30 p-5">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{t("consulterJurisprudence.notionsIdentifiees")}</p>
            <div className="flex flex-wrap gap-2">
              {data.notions.domaine && <span className="badge border-gold-600/30 bg-surface-2 text-gold-500">{data.notions.domaine}</span>}
              {data.notions.qualification_juridique && (
                <span className="badge border-gold-600/30 bg-surface-2 text-warmgray">{data.notions.qualification_juridique}</span>
              )}
            </div>
            {data.notions.mots_cles_recherche.length > 0 && (
              <p className="text-xs text-muted">{t("consulterJurisprudence.motsCles")} {data.notions.mots_cles_recherche.join(", ")}</p>
            )}
          </div>

          <div className="card p-6">
            <RichOutput texte={data.reponse} />
          </div>

          {data.diagnostic && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">{t("arsenal.diagnostic")}</h2><p className="whitespace-pre-wrap text-sm text-warmgray">{data.diagnostic}</p></div>}
          {data.strategie && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">{t("arsenal.strategie")}</h2><p className="whitespace-pre-wrap text-sm text-ivory">{data.strategie}</p></div>}

          <VerificationPanel verification={data.verification} />

          <ChatContextuelPanel
            feature="jurisprudence_consultation"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            documentId={data.document_id}
            placeholder={t("consulterJurisprudence.chatPlaceholder")}
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre={t("consulterJurisprudence.pretTitre")}
          description={t("consulterJurisprudence.pretDescription")}
        />
      )}
    </div>
  );
}
