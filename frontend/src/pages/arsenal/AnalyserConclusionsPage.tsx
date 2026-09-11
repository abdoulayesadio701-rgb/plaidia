/**
 * AnalyserConclusionsPage — /arsenal/analyser. Colle ou importe le texte
 * des conclusions adverses, appelle POST /api/analyse/conclusions.
 * Sauvegarde automatique côté serveur dans l'historique du dossier dès
 * que dossier_id est transmis (voir backend/app/routers/analyse.py) — pas
 * de logique de sauvegarde à écrire ici, juste à le signaler à l'écran.
 */

import { useCallback, useState } from "react";
import { analyse as analyseApi } from "@/api";
import type { StatutDocument } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyStream } from "@/hooks/useLazyStream";
import { useImportTexte } from "@/hooks/useImportTexte";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import ArgumentCard from "@/components/ArgumentCard";
import ChoixImportModal from "@/components/ChoixImportModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import EtapePipelineIndicator from "@/components/EtapePipelineIndicator";
import FileDropZone from "@/components/FileDropZone";
import PinButton from "@/components/PinButton";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";
import VerificationPanel from "@/components/VerificationPanel";
import StatutDocumentMenu, { StatutDocumentBadge } from "@/components/StatutDocument";
import type { ConclusionsResultat } from "@/api/types";

export default function AnalyserConclusionsPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [texte, setTexte] = useState("");
  const [changementStatutEnCours, setChangementStatutEnCours] = useState(false);

  const lancerFlux = useCallback(
    (t: string, cb: Parameters<typeof analyseApi.streamAnalyserConclusions>[2], signal: AbortSignal) =>
      analyseApi.streamAnalyserConclusions(t, dossierActif?.id, cb, signal),
    [dossierActif?.id]
  );
  const { data, etape, loading, error, executer, definirDonnees } = useLazyStream<ConclusionsResultat, [string]>(lancerFlux);
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: dossierActif?.id ?? null,
    getTexteActuel: () => texte,
    onTexteExtrait: setTexte,
  });

  const changerStatut = async (statut: StatutDocument) => {
    if (!data?.analyse_id) return;
    setChangementStatutEnCours(true);
    try {
      await analyseApi.changerStatutConclusion(data.analyse_id, statut);
      definirDonnees({ ...data, statut });
      pousserToast("success", `Document passé au statut « ${statut} ».`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Impossible de changer le statut.");
    } finally {
      setChangementStatutEnCours(false);
    }
  };

  if (!dossierActif) {
    return (
      <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour analyser des conclusions adverses." />
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">L'Arsenal</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Analyser des conclusions adverses</h1>
        <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          {...dragProps}
          className={`input min-h-[220px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
          placeholder="Collez ici le texte des conclusions adverses, ou déposez un fichier…"
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
            <span className="text-xs text-muted">PDF, Word, Excel, image — le texte extrait est aussi ajouté aux faits du dossier.</span>
          </div>
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={() => void executer(texte)}>
            Analyser
          </Button>
        </div>
      </div>

      {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

      {loading && !data?.arguments && <SkeletonList count={3} />}

      {loading && <EtapePipelineIndicator etape={etape} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer(texte)} />}

      {!error && data?.arguments && (
        <div className="space-y-5">
          {data.analyse_id != null && (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <p className="text-xs text-warmgray">✓ Enregistré dans l'historique de ce dossier.</p>
                <StatutDocumentBadge statut={data.statut} />
              </div>
              <div className="flex items-center gap-2">
                <StatutDocumentMenu statut={data.statut} loading={changementStatutEnCours} onChange={changerStatut} />
                <PinButton
                  type="analyse"
                  referenceId={data.analyse_id}
                  dossierId={dossierActif.id}
                  libelle={`Analyse — ${dossierActif.nom}`}
                />
              </div>
            </div>
          )}
          {data.diagnostic && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">Diagnostic</h2><p className="whitespace-pre-wrap text-sm text-warmgray">{data.diagnostic}</p></div>}
          {data.strategie && <div className="card"><h2 className="mb-2 font-serif text-h4 text-gold-500">Stratégie pour la partie représentée</h2><p className="whitespace-pre-wrap text-sm text-ivory">{data.strategie}</p></div>}

          {data.statut === "Final" && (
            <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-4 text-sm text-gold-500">
              Ce document est Final et peut uniquement être consulté.
            </div>
          )}

          {data.arguments.length === 0 ? (
            <EmptyState
              titre="Aucun argument identifié"
              description="Le texte fourni ne ressemble pas à des conclusions juridiques, ou aucun argument n'a pu en être extrait."
            />
          ) : (
            data.arguments.map((arg, i) => <ArgumentCard key={i} argument={arg} index={i} />)
          )}

          {data.points_attention.length > 0 && (
            <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
              <p className="mb-2 text-sm font-semibold text-risk-high">⚠ Points d'attention</p>
              <ul className="space-y-1.5">
                {data.points_attention.map((p, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-risk-high">•</span>
                    <RichOutput texte={p} prose={false} className="flex-1 text-sm" />
                  </li>
                ))}
              </ul>
            </div>
          )}

          <VerificationPanel verification={data.verification} />

          {data.statut !== "Final" && (
            <ChatContextuelPanel feature="conclusions" resultatActuel={data} onMiseAJour={definirDonnees} dossierId={dossierActif.id} />
          )}
        </div>
      )}

      {!loading && !error && !data?.arguments && (
        <EmptyState
          titre="Prêt à analyser"
          description="Collez le texte des conclusions adverses ci-dessus, ou importez un fichier, puis cliquez sur « Analyser »."
        />
      )}
    </div>
  );
}
