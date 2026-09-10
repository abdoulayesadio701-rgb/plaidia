/**
 * VersionsHistorique — historique des versions d'un résultat édité via le
 * chat contextuel (voir AUDIT_TASKBAR.md, étape 4). Une version est créée
 * automatiquement côté serveur à chaque patch appliqué (voir
 * routers/chat.py::chat_contextuel) -- ce composant se contente de lister
 * et de proposer une restauration, jamais de supprimer quoi que ce soit.
 *
 * Monté dans ChatContextuelPanel : même paire (feature, dossierId) que le
 * fil de discussion, puisque les versions naissent des éditions de ce fil.
 */

import { useEffect, useState } from "react";
import { versions as versionsApi } from "@/api";
import type { VersionDocument } from "@/api";
import { useAppStore } from "@/store/useAppStore";

const LIBELLE_AUTEUR: Record<string, string> = { ia: "IA", utilisateur: "Restauration" };

function formaterDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("fr-FR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

interface VersionsHistoriqueProps<T> {
  feature: string;
  dossierId?: number | null;
  documentId?: number | null;
  onRestaurer: (contenu: T) => void;
}

export default function VersionsHistorique<T>({ feature, dossierId, documentId, onRestaurer }: VersionsHistoriqueProps<T>) {
  const [ouvert, setOuvert] = useState(false);
  const [liste, setListe] = useState<VersionDocument[]>([]);
  const [chargement, setChargement] = useState(false);
  const [idEnCours, setIdEnCours] = useState<number | null>(null);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const charger = async () => {
    setChargement(true);
    try {
      setListe(await versionsApi.listerVersions(feature, dossierId, documentId));
    } catch {
      // L'historique reste simplement vide si le backend n'est pas joignable -- non bloquant.
    } finally {
      setChargement(false);
    }
  };

  useEffect(() => {
    if (ouvert) void charger();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ouvert]);

  const restaurer = async (version: VersionDocument) => {
    setIdEnCours(version.id);
    try {
      const restauree = await versionsApi.restaurerVersion(version.id);
      onRestaurer(restauree.contenu as T);
      pousserToast("success", `Version du ${formaterDate(version.date_creation)} restaurée.`);
      await charger();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "La restauration a échoué.");
    } finally {
      setIdEnCours(null);
    }
  };

  return (
    <div>
      <button type="button" onClick={() => setOuvert((v) => !v)} className="text-xs text-muted hover:text-warmgray">
        🔄 Versions{liste.length > 0 ? ` (${liste.length})` : ""}
      </button>

      {ouvert && (
        <div className="mt-2 space-y-1.5 rounded-md bg-surface-2/60 p-2.5">
          {chargement && <p className="text-xs text-warmgray">Chargement…</p>}
          {!chargement && liste.length === 0 && <p className="text-xs text-warmgray">Aucune version enregistrée pour l'instant.</p>}
          {!chargement &&
            liste.map((v, i) => (
              <div key={v.id} className="flex items-center justify-between gap-2 rounded-md bg-surface px-2.5 py-1.5 text-xs">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-ivory">{v.resume_modification || (i === liste.length - 1 ? "Version initiale" : "Modification")}</p>
                  <p className="text-muted">
                    {formaterDate(v.date_creation)} · {LIBELLE_AUTEUR[v.auteur] ?? v.auteur}
                  </p>
                </div>
                <button
                  onClick={() => void restaurer(v)}
                  disabled={idEnCours !== null || i === 0}
                  className="shrink-0 text-amethyst-400 hover:underline disabled:cursor-not-allowed disabled:text-muted disabled:no-underline"
                  title={i === 0 ? "Déjà la version actuelle" : "Restaurer cette version"}
                >
                  {idEnCours === v.id ? "…" : i === 0 ? "Actuelle" : "Restaurer"}
                </button>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
