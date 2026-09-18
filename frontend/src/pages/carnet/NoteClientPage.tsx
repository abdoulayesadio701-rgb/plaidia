/**
 * NoteClientPage — /carnet/note-client. Génère une note de synthèse en
 * langage simple pour le client (voir analyse.py::rediger_note_client),
 * avec copie presse-papiers et export Word.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { analyse as analyseApi, notes as notesApi, downloadBlob } from "@/api";
import type { NoteClientResultat } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useDernierDocumentGenere } from "@/hooks/useDernierDocumentGenere";
import Button from "@/components/Button";
import ConfirmerModal from "@/components/ConfirmerModal";
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
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);

  const { data, loading, error, executer, definirDonnees, reinitialiser } = useLazyAction(() => notesApi.redigerNoteClient(dossierActif!.id));
  // Recharge automatiquement, au montage, la dernière note client déjà
  // persistée pour ce dossier -- une simple lecture, jamais un nouvel
  // appel IA -- pour qu'elle reste visible après une navigation ou un
  // refresh complet.
  const { document: dernierDocument, loading: dernierDocumentLoading } = useDernierDocumentGenere(dossierActif?.id, "note_client");

  useEffect(() => {
    if (!dernierDocument || data) return;
    definirDonnees({ ...(dernierDocument.contenu as unknown as NoteClientResultat), document_id: dernierDocument.id, statut: dernierDocument.statut });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dernierDocument]);

  const supprimer = async () => {
    if (!data?.document_id) return;
    setSuppressionEnCours(true);
    try {
      await analyseApi.supprimerDocumentGenere(data.document_id);
      reinitialiser();
      setConfirmationSuppression(false);
      pousserToast("success", t("arsenal.resultatSupprime"));
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("arsenal.erreurSuppression"));
    } finally {
      setSuppressionEnCours(false);
    }
  };

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

      {(loading || dernierDocumentLoading) && <SkeletonList count={2} />}

      {!loading && !dernierDocumentLoading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !dernierDocumentLoading && !error && data && (
        <div className="space-y-4">
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => void copier()}>
              📋 {t("noteClient.copier")}
            </Button>
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ {t("arsenal.exporterWord")}
            </Button>
            {data.document_id && (
              <Button variant="ghost" onClick={() => setConfirmationSuppression(true)}>🗑 {t("commun.supprimer")}</Button>
            )}
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

      {!loading && !dernierDocumentLoading && !error && !data && (
        <EmptyState
          titre={t("rapportComplet.pretTitre")}
          description={t("noteClient.pretDescription")}
        />
      )}

      {confirmationSuppression && (
        <ConfirmerModal
          titre={t("arsenal.confirmerSuppressionTitre")}
          description={t("arsenal.confirmerSuppressionDescription")}
          texteBouton={t("commun.supprimer")}
          enCours={suppressionEnCours}
          onFermer={() => setConfirmationSuppression(false)}
          onConfirmer={supprimer}
        />
      )}
    </div>
  );
}
