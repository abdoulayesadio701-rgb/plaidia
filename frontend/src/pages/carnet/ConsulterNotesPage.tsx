/**
 * ConsulterNotesPage — /carnet/notes. Timeline des notes du dossier actif,
 * groupées par jour (déjà triées du plus récent au plus ancien côté
 * backend, voir db.py::get_notes_dossier).
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { notes as notesApi } from "@/api";
import type { Note } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";

function formaterJour(iso: string, langue: string): string {
  try {
    const locale = langue === "en" ? "en-GB" : "fr-FR";
    return new Date(iso).toLocaleDateString(locale, { weekday: "long", day: "2-digit", month: "long", year: "numeric" });
  } catch {
    return iso;
  }
}

function formaterHeure(iso: string, langue: string): string {
  try {
    const locale = langue === "en" ? "en-GB" : "fr-FR";
    return new Date(iso).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

export default function ConsulterNotesPage() {
  const { t, i18n } = useTranslation();
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);

  const { data: notes, loading, error, reload } = useAsync(() => notesApi.listerNotes(dossierActif!.id), [dossierActif?.id], dossierActif !== null);

  if (!dossierActif) {
    return <EmptyState titre={t("consulterNotes.emptyTitre")} description={t("consulterNotes.emptyDescription")} />;
  }

  const groupes = new Map<string, Note[]>();
  for (const n of notes ?? []) {
    const jour = n.date_creation.slice(0, 10);
    if (!groupes.has(jour)) groupes.set(jour, []);
    groupes.get(jour)!.push(n);
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.carnet")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("consulterNotes.titre")}</h1>
        <p className="mt-2 text-sm text-warmgray">{t("arsenal.dossierActif")} : {dossierActif.nom}</p>
      </div>

      {loading && <SkeletonList count={3} />}

      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && notes && notes.length === 0 && (
        <EmptyState titre={t("consulterNotes.aucuneNoteTitre")} description={t("consulterNotes.aucuneNoteDescription")} />
      )}

      {!loading &&
        !error &&
        [...groupes.entries()].map(([jour, notesDuJour]) => (
          <div key={jour} className="space-y-3">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{formaterJour(notesDuJour[0].date_creation, i18n.language)}</p>
            <div className="relative space-y-4 border-l-2 border-gold-600/25 pl-6">
              {notesDuJour.map((note) => (
                <NoteItem key={note.id} note={note} onSupprime={reload} onErreur={(m) => pousserToast("error", m)} t={t} langue={i18n.language} />
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}

interface NoteItemProps {
  note: Note;
  onSupprime: () => void;
  onErreur: (message: string) => void;
  t: TFunction;
  langue: string;
}

function NoteItem({ note, onSupprime, onErreur, t, langue }: NoteItemProps) {
  const [confirmation, setConfirmation] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);

  const supprimer = async () => {
    setSuppressionEnCours(true);
    try {
      await notesApi.supprimerNote(note.id);
      onSupprime();
    } catch (e) {
      onErreur(e instanceof Error ? e.message : t("dossiersPage.echecSuppression"));
      setSuppressionEnCours(false);
      setConfirmation(false);
    }
  };

  return (
    <div className="relative">
      <span className="absolute -left-[27px] top-1.5 h-2.5 w-2.5 rounded-pill bg-gold-500" aria-hidden="true" />
      <div className="card space-y-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <span className="text-xs text-muted">{formaterHeure(note.date_creation, langue)}</span>
          {!confirmation ? (
            <button onClick={() => setConfirmation(true)} className="text-xs text-muted hover:text-risk-high">
              {t("consulterNotes.supprimer")}
            </button>
          ) : (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-warmgray">{t("consulterNotes.confirmer")}</span>
              <button disabled={suppressionEnCours} onClick={() => void supprimer()} className="font-semibold text-risk-high hover:underline">
                {t("consulterNotes.oui")}
              </button>
              <button onClick={() => setConfirmation(false)} className="text-warmgray hover:underline">
                {t("commun.annuler")}
              </button>
            </div>
          )}
        </div>

        <RichOutput texte={note.note_structuree || note.note_brute} prose={false} className="text-sm" />

        {(note.actions.length > 0 || note.points.length > 0) && (
          <div className="grid grid-cols-1 gap-3 border-t border-gold-600/15 pt-3 sm:grid-cols-2">
            {note.actions.length > 0 && (
              <div>
                <p className="mb-1 text-micro font-medium uppercase tracking-wide text-gold-500">{t("consulterNotes.actions")}</p>
                <ul className="space-y-1 text-sm text-warmgray">
                  {note.actions.map((a, i) => (
                    <li key={i}>· {a}</li>
                  ))}
                </ul>
              </div>
            )}
            {note.points.length > 0 && (
              <div>
                <p className="mb-1 text-micro font-medium uppercase tracking-wide text-gold-500">{t("prendreNote.pointsARetenir")}</p>
                <ul className="space-y-1 text-sm text-warmgray">
                  {note.points.map((p, i) => (
                    <li key={i}>· {p}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
