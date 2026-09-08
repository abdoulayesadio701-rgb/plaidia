/**
 * ChronologiePage — /greffier/chronologie. Timeline verticale des
 * événements datés du dossier actif, période couverte, éléments manquants.
 * Verticale plutôt qu'horizontale : cohérent avec PlanTimeline et
 * l'accordéon d'historique de La Chemise (même vocabulaire visuel dans
 * toute l'app), et lisible sans limite de largeur pour un nombre
 * d'événements variable.
 */

import { useState } from "react";
import { greffier as greffierApi, downloadBlob } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

export default function ChronologiePage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [exportEnCours, setExportEnCours] = useState(false);
  const { data, loading, error, executer, definirDonnees } = useLazyAction(() => greffierApi.chronologie(dossierActif!.id));

  const exporter = async () => {
    if (!dossierActif || !data) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await greffierApi.exporterChronologie(dossierActif.id, data);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_chronologie.csv`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'export.");
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour construire sa chronologie." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">Le Greffier</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Chronologie automatique</h1>
          <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {data && (
            <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
              ⬇ Exporter en CSV
            </Button>
          )}
          <Button variant="primary" loading={loading} onClick={() => void executer()}>
            {data ? "↻ Régénérer" : "Construire la chronologie"}
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-6">
          <p className="flex items-center gap-2 text-sm text-warmgray">
            Période couverte
            <span className="badge border-amethyst-400/40 bg-amethyst-400/10 text-amethyst-400">{data.periode_couverte}</span>
          </p>

          {data.evenements.length === 0 ? (
            <EmptyState titre="Aucun événement daté identifié" description="Le contenu du dossier ne contient pas assez d'éléments datés pour construire une chronologie." />
          ) : (
            <div className="relative space-y-5 border-l-2 border-gold-600/25 pl-8">
              {data.evenements.map((ev, i) => (
                <div key={i} className="relative">
                  <span className="absolute -left-[38px] flex h-6 w-6 items-center justify-center rounded-pill border-2 border-gold-600 bg-void font-mono text-xs text-gold-500">
                    {i + 1}
                  </span>
                  <div className="card space-y-1 p-4">
                    <p className="font-mono text-xs font-semibold text-amethyst-400">{ev.date}</p>
                    <p className="text-sm text-ivory">{ev.evenement}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {data.elements_manquants.length > 0 && (
            <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-5">
              <p className="mb-2 text-sm font-semibold text-gold-500">Éléments manquants</p>
              <ul className="space-y-1.5 text-sm text-ivory">
                {data.elements_manquants.map((el, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-gold-500">•</span>
                    {el}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <ChatContextuelPanel
            feature="chronologie"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            placeholder="Ex. « Ajoute cet événement : … », « pourquoi cet élément est-il manquant ? »…"
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à construire la chronologie" description="Cliquez sur « Construire la chronologie » pour ordonner les événements datés du dossier." />
      )}
    </div>
  );
}
