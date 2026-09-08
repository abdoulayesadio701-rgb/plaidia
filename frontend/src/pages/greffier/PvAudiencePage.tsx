/**
 * PvAudiencePage — /greffier/pv-audience. Notes brutes à gauche, PV généré
 * et éditable à droite, export Word. Indépendant de tout dossier -- un PV
 * peut être rédigé avant même la création d'une affaire (voir
 * export.py::exporter_texte_libre_word, exposé via POST
 * /api/greffier/pv-audience/export ajouté pour cette page).
 */

import { useState } from "react";
import { dossiers as dossiersApi, greffier as greffierApi, downloadBlob } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import { SkeletonBlock } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

export default function PvAudiencePage() {
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [notes, setNotes] = useState("");
  const [pvTexte, setPvTexte] = useState("");
  const [exportEnCours, setExportEnCours] = useState(false);
  const [enImport, setEnImport] = useState(false);

  const { loading, error, executer } = useLazyAction((n: string) => greffierApi.pvAudience(n));

  const generer = async () => {
    const resultat = await executer(notes);
    if (resultat) setPvTexte(resultat.texte);
  };

  const importerFichier = async (fichier: File) => {
    setEnImport(true);
    try {
      const resultat = await dossiersApi.extraireFichier(fichier);
      setNotes((precedent) => (precedent ? `${precedent}\n\n${resultat.texte_extrait}` : resultat.texte_extrait));
      pousserToast("success", `« ${resultat.nom_fichier} » importé (${resultat.caracteres_extraits.toLocaleString("fr-FR")} caractères).`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'import du fichier.");
    } finally {
      setEnImport(false);
    }
  };

  const copier = async () => {
    try {
      await navigator.clipboard.writeText(pvTexte);
      pousserToast("success", "PV copié dans le presse-papiers.");
    } catch {
      pousserToast("error", "Impossible d'accéder au presse-papiers.");
    }
  };

  const exporter = async () => {
    setExportEnCours(true);
    try {
      const { blob, filename } = await greffierApi.exporterPvAudience(pvTexte);
      downloadBlob(blob, filename ?? "proces_verbal_audience.docx");
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'export.");
    } finally {
      setExportEnCours(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="kicker">Le Greffier</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Rédaction d'un procès-verbal d'audience</h1>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card flex flex-col gap-3 p-6">
          <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">Notes brutes</p>
          <textarea
            className="input min-h-[380px] flex-1 resize-y"
            placeholder="Notez librement ce qui se dit pendant l'audience – l'agent les met en forme en PV structuré."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={loading || enImport}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <FileDropZone
                variante="compact"
                extensions={EXTENSIONS_DOCUMENT}
                loading={enImport}
                disabled={loading}
                onFichiers={(fichiers) => void importerFichier(fichiers[0])}
              />
            </div>
            <Button variant="primary" loading={loading} disabled={!notes.trim() || enImport} onClick={() => void generer()}>
              {pvTexte ? "↻ Régénérer le PV" : "Générer le PV"}
            </Button>
          </div>
        </div>

        <div className="card flex flex-col gap-3 p-6">
          <div className="flex items-center justify-between gap-3">
            <p className="text-micro font-medium uppercase tracking-wide text-gold-500">PV généré (éditable)</p>
            {pvTexte && !loading && (
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => void copier()}>
                  📋 Copier
                </Button>
                <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
                  ⬇ Exporter en Word
                </Button>
              </div>
            )}
          </div>

          {loading && (
            <div className="flex-1 space-y-2.5">
              <SkeletonBlock className="h-4 w-full" />
              <SkeletonBlock className="h-4 w-11/12" />
              <SkeletonBlock className="h-4 w-full" />
              <SkeletonBlock className="h-4 w-4/5" />
            </div>
          )}

          {!loading && error && <ErrorState message={error} onRetry={() => void generer()} />}

          {!loading && !error && pvTexte && (
            <>
              <textarea
                className="input min-h-[380px] flex-1 resize-y font-serif text-[1.02rem] leading-relaxed"
                value={pvTexte}
                onChange={(e) => setPvTexte(e.target.value)}
              />
              <ChatContextuelPanel
                feature="pv_audience"
                resultatActuel={{ texte: pvTexte }}
                onMiseAJour={(r) => setPvTexte(r.texte)}
                placeholder="Ex. « Rends le style plus formel », « raccourcis le deuxième paragraphe »…"
              />
            </>
          )}

          {!loading && !error && !pvTexte && (
            <div className="flex flex-1 items-center">
              <EmptyState titre="En attente" description="Rédigez vos notes à gauche, puis cliquez sur « Générer le PV »." />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
