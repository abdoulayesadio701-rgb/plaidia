/**
 * NoteClientPage — /carnet/note-client. Génère une note de synthèse en
 * langage simple pour le client (voir analyse.py::rediger_note_client),
 * avec copie presse-papiers et export Word.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [exportEnCours, setExportEnCours] = useState(false);

  const { data, loading, error, executer, definirDonnees } = useLazyAction(() => notesApi.redigerNoteClient(dossierActif!.id));

  const copier = async () => {
    if (!data) return;
    try {
      await navigator.clipboard.writeText(data.texte);
      pousserToast("success", t("noteClient.copiee"));
    } catch {
      pousserToast("error", t("noteClient.echecPressePapiers"));
    }
  };

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await notesApi.exporterNoteClient(dossierActif.id, data.texte);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_note_client.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.echecExport"));
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre={t("noteClient.emptyTitre")} description={t("noteClient.emptyDescription")} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{t("nav.sections.carnet")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.carnet.note-client")}</h1>
          <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
        </div>
        <Button variant="primary" loading={loading} onClick={() => void executer()}>
          {data ? `↻ ${t("noteClient.regenerer")}` : t("noteClient.generer")}
        </Button>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-4">
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => void copier()}>
              📋 {t("noteClient.copier")}
            </Button>
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
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
            placeholder={t("noteClient.chatPlaceholder")}
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre={t("rapportComplet.pretTitre")}
          description={t("noteClient.pretDescription")}
        />
      )}
    </div>
  );
}
