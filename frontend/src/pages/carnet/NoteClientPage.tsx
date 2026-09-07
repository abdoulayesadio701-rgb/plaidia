/**
 * NoteClientPage — /carnet/note-client. Génère une note de synthèse en
 * langage simple pour le client (voir analyse.py::rediger_note_client),
 * avec copie presse-papiers et export Word.
 */

import { useState } from "react";
import { notes as notesApi, downloadBlob } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

export default function NoteClientPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [exportEnCours, setExportEnCours] = useState(false);

  const { data, loading, error, executer, definirDonnees } = useLazyAction(() => notesApi.redigerNoteClient(dossierActif!.id));

  const copier = async () => {
    if (!data) return;
    try {
      await navigator.clipboard.writeText(data.texte);
      pousserToast("success", "Note client copiée dans le presse-papiers.");
    } catch {
      pousserToast("error", "Impossible d'accéder au presse-papiers.");
    }
  };

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await notesApi.exporterNoteClient(dossierActif.id, data.texte);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_note_client.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'export.");
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour rédiger sa note client." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">Le Carnet</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Note client</h1>
          <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
        </div>
        <Button variant="primary" loading={loading} onClick={() => void executer()}>
          {data ? "↻ Régénérer" : "Générer la note client"}
        </Button>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-4">
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => void copier()}>
              📋 Copier
            </Button>
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ Exporter en Word
            </Button>
          </div>
          <div className="card p-6">
            <RichOutput texte={data.texte} />
          </div>

          <ChatContextuelPanel
            feature="note_client"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            placeholder="Ex. « Rends le ton plus rassurant », « fais plus court », « moins technique »…"
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre="Prêt à générer"
          description="Rédige une synthèse en langage simple des faits, des enjeux et des prochaines étapes du dossier, à destination du client."
        />
      )}
    </div>
  );
}
