/**
 * PrendreNotePage — /carnet/note. Saisie en vrac, structurée par l'IA en
 * note propre + actions à faire + points à retenir (voir
 * analyse.py::traiter_notes). Les cases à cocher sont un pense-bête local,
 * non persisté -- le backend n'expose pas d'état "fait/pas fait" par action.
 */

import { useState } from "react";
import { notes as notesApi } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";

export default function PrendreNotePage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [texte, setTexte] = useState("");
  const [actionsCochees, setActionsCochees] = useState<Set<number>>(new Set());

  const { data, loading, error, executer } = useLazyAction((t: string) => notesApi.creerNote(dossierActif!.id, t));

  const soumettre = async () => {
    const resultat = await executer(texte);
    if (resultat) {
      setTexte("");
      setActionsCochees(new Set());
      pousserToast("success", "Note enregistrée.");
    }
  };

  const basculerAction = (i: number) =>
    setActionsCochees((s) => {
      const copie = new Set(s);
      if (copie.has(i)) copie.delete(i);
      else copie.add(i);
      return copie;
    });

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour y prendre une note." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">Le Carnet</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Prendre une note</h1>
        <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          className="input min-h-[180px] resize-y"
          placeholder="Notez librement, en vrac -- l'agent structure, extrait les actions à faire et les points à retenir."
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          disabled={loading}
        />
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} disabled={!texte.trim()} onClick={() => void soumettre()}>
            Structurer la note
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void soumettre()} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="card p-6">
            <p className="mb-2 text-micro font-medium uppercase tracking-wide text-amethyst-400">Note</p>
            <RichOutput texte={data.note_structuree || data.note_brute} />
          </div>

          {data.actions.length > 0 && (
            <div className="card space-y-3 p-6">
              <p className="text-micro font-medium uppercase tracking-wide text-gold-500">Actions à faire</p>
              <ul className="space-y-2">
                {data.actions.map((a, i) => (
                  <li key={i}>
                    <label className="flex cursor-pointer items-start gap-2.5 text-sm">
                      <input
                        type="checkbox"
                        checked={actionsCochees.has(i)}
                        onChange={() => basculerAction(i)}
                        className="mt-0.5 h-4 w-4 shrink-0 rounded accent-amethyst-400"
                      />
                      <span className={actionsCochees.has(i) ? "text-muted line-through" : "text-ivory"}>{a}</span>
                    </label>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-muted">Coché localement pour votre suivi -- non enregistré sur le serveur.</p>
            </div>
          )}

          {data.points.length > 0 && (
            <div className="card space-y-2 p-6">
              <p className="text-micro font-medium uppercase tracking-wide text-gold-500">Points à retenir</p>
              <ul className="space-y-1.5">
                {data.points.map((p, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ivory">
                    <span className="text-gold-500">•</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à structurer" description="Écrivez votre note ci-dessus, dans l'ordre qui vous vient, puis cliquez sur « Structurer la note »." />
      )}
    </div>
  );
}
