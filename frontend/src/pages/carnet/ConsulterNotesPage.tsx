/**
 * ConsulterNotesPage — /carnet/notes. Timeline des notes du dossier actif,
 * groupées par jour (déjà triées du plus récent au plus ancien côté
 * backend, voir db.py::get_notes_dossier).
 */

import { useState } from "react";
import { notes as notesApi } from "@/api";
import type { Note } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";

function formaterJour(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("fr-FR", { weekday: "long", day: "2-digit", month: "long", year: "numeric" });
  } catch {
    return iso;
  }
}

function formaterHeure(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

export default function ConsulterNotesPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);

  const { data: notes, loading, error, reload } = useAsync(() => notesApi.listerNotes(dossierActif!.id), [dossierActif?.id], dossierActif !== null);

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour consulter ses notes." />;
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
        <p className="kicker">Le Carnet</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Notes du dossier</h1>
        <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
      </div>

      {loading && <SkeletonList count={3} />}

      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && notes && notes.length === 0 && (
        <EmptyState titre="Aucune note pour l'instant" description="Utilisez « Prendre une note » pour commencer à journaliser ce dossier." />
      )}

      {!loading &&
        !error &&
        [...groupes.entries()].map(([jour, notesDuJour]) => (
          <div key={jour} className="space-y-3">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{formaterJour(notesDuJour[0].date_creation)}</p>
            <div className="relative space-y-4 border-l-2 border-gold-600/25 pl-6">
              {notesDuJour.map((note) => (
                <NoteItem key={note.id} note={note} onSupprime={reload} onErreur={(m) => pousserToast("error", m)} />
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
}

function NoteItem({ note, onSupprime, onErreur }: NoteItemProps) {
  const [confirmation, setConfirmation] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);

  const supprimer = async () => {
    setSuppressionEnCours(true);
    try {
      await notesApi.supprimerNote(note.id);
      onSupprime();
    } catch (e) {
      onErreur(e instanceof Error ? e.message : "La suppression a échoué.");
      setSuppressionEnCours(false);
      setConfirmation(false);
    }
  };

  return (
    <div className="relative">
      <span className="absolute -left-[27px] top-1.5 h-2.5 w-2.5 rounded-pill bg-gold-500" aria-hidden="true" />
      <div className="card space-y-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <span className="text-xs text-muted">{formaterHeure(note.date_creation)}</span>
          {!confirmation ? (
            <button onClick={() => setConfirmation(true)} className="text-xs text-muted hover:text-risk-high">
              Supprimer
            </button>
          ) : (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-warmgray">Confirmer ?</span>
              <button disabled={suppressionEnCours} onClick={() => void supprimer()} className="font-semibold text-risk-high hover:underline">
                Oui
              </button>
              <button onClick={() => setConfirmation(false)} className="text-warmgray hover:underline">
                Annuler
              </button>
            </div>
          )}
        </div>

        <RichOutput texte={note.note_structuree || note.note_brute} prose={false} className="text-sm" />

        {(note.actions.length > 0 || note.points.length > 0) && (
          <div className="grid grid-cols-1 gap-3 border-t border-gold-600/15 pt-3 sm:grid-cols-2">
            {note.actions.length > 0 && (
              <div>
                <p className="mb-1 text-micro font-medium uppercase tracking-wide text-gold-500">Actions</p>
                <ul className="space-y-1 text-sm text-warmgray">
                  {note.actions.map((a, i) => (
                    <li key={i}>· {a}</li>
                  ))}
                </ul>
              </div>
            )}
            {note.points.length > 0 && (
              <div>
                <p className="mb-1 text-micro font-medium uppercase tracking-wide text-gold-500">Points à retenir</p>
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
