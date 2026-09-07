/**
 * AnalyserConclusionsPage — /arsenal/analyser. Colle ou importe le texte
 * des conclusions adverses, appelle POST /api/analyse/conclusions.
 * Sauvegarde automatique côté serveur dans l'historique du dossier dès
 * que dossier_id est transmis (voir backend/app/routers/analyse.py) — pas
 * de logique de sauvegarde à écrire ici, juste à le signaler à l'écran.
 */

import { useRef, useState } from "react";
import { analyse as analyseApi, dossiers as dossiersApi } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import ArgumentCard from "@/components/ArgumentCard";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

const EXTENSIONS_ACCEPTEES = ".pdf,.docx,.xlsx,.xls,.txt,.png,.jpg,.jpeg,.webp";

export default function AnalyserConclusionsPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [texte, setTexte] = useState("");
  const [enImport, setEnImport] = useState(false);
  const inputFichierRef = useRef<HTMLInputElement>(null);

  const { data, loading, error, executer, definirDonnees } = useLazyAction((t: string) => analyseApi.analyserConclusions(t, dossierActif?.id));

  const importerFichier = async (fichier: File) => {
    if (!dossierActif) return;
    setEnImport(true);
    try {
      const resultat = await dossiersApi.importerDocument(dossierActif.id, fichier);
      setTexte((precedent) => (precedent ? `${precedent}\n\n${resultat.texte_extrait}` : resultat.texte_extrait));
      pousserToast(
        "success",
        `« ${resultat.nom_fichier} » importé (${resultat.caracteres_extraits.toLocaleString("fr-FR")} caractères) – également ajouté aux faits du dossier.`
      );
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'import du fichier.");
    } finally {
      setEnImport(false);
      if (inputFichierRef.current) inputFichierRef.current.value = "";
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
          className="input min-h-[220px] resize-y"
          placeholder="Collez ici le texte des conclusions adverses…"
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          disabled={loading || enImport}
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={inputFichierRef}
              type="file"
              accept={EXTENSIONS_ACCEPTEES}
              className="hidden"
              onChange={(e) => {
                const fichier = e.target.files?.[0];
                if (fichier) void importerFichier(fichier);
              }}
            />
            <Button variant="secondary" loading={enImport} disabled={loading} onClick={() => inputFichierRef.current?.click()}>
              📎 Importer un fichier
            </Button>
            <span className="text-xs text-muted">PDF, Word, Excel, image — le texte extrait est aussi ajouté aux faits du dossier.</span>
          </div>
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={() => void executer(texte)}>
            Analyser
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={3} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer(texte)} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          {data.analyse_id != null && <p className="text-xs text-warmgray">✓ Enregistré dans l'historique de ce dossier.</p>}

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

          <ChatContextuelPanel feature="conclusions" resultatActuel={data} onMiseAJour={definirDonnees} dossierId={dossierActif.id} />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre="Prêt à analyser"
          description="Collez le texte des conclusions adverses ci-dessus, ou importez un fichier, puis cliquez sur « Analyser »."
        />
      )}
    </div>
  );
}
