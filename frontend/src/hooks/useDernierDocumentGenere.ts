/**
 * useDernierDocumentGenere — relecture automatique, au montage d'une page
 * Arsenal, du dernier résultat déjà persisté pour ce dossier+feature (voir
 * db.creer_document_genere / documents_generes). Comble le trou laissé par
 * useAsync/useLazyAction : ces derniers gardent leur résultat en state local
 * de composant, perdu dès que la page est démontée (navigation, refresh) --
 * ce hook redonne au montage ce que le backend a déjà en base, SANS relancer
 * l'IA (règle de useLazyAction.ts : un appel IA n'est jamais automatique,
 * ceci n'est qu'une lecture GET).
 *
 * `listerDocumentsGeneres` (dossiers.ts) renvoie déjà le plus récent en
 * premier (db.lister_documents_generes, tri DESC par date_modification) --
 * on prend donc simplement le premier élément.
 */

import { dossiers as dossiersApi } from "@/api";
import type { DocumentGenere } from "@/api";
import { useAsync } from "./useAsync";

export function useDernierDocumentGenere(
  dossierId: number | undefined,
  feature: string,
  enabled = true
): { document: DocumentGenere | null; loading: boolean; error: string | null } {
  const { data, loading, error } = useAsync(
    () => dossiersApi.listerDocumentsGeneres(dossierId!, feature),
    [dossierId, feature],
    enabled && dossierId !== undefined
  );
  return { document: data && data.length > 0 ? data[0] : null, loading, error };
}

/**
 * Variante pour les conclusions (table `analyses`, distincte de
 * `documents_generes` -- voir db.py section "Générations"/"analyses").
 * `historiqueAnalyses` (dossiers.ts) renvoie déjà le plus récent en premier
 * (db.get_analyses_for_dossier, tri DESC par date).
 *
 * Limite assumée : la table `analyses` ne stocke que arguments +
 * points_attention + statut, pas diagnostic/strategie/verification -- la
 * relecture restaure donc le cœur du résultat, pas ces champs annexes
 * recalculés à chaque génération.
 */
export function useDerniereAnalyseConclusions(dossierId: number | undefined, enabled = true) {
  const { data, loading, error } = useAsync(
    () => dossiersApi.historiqueAnalyses(dossierId!),
    [dossierId],
    enabled && dossierId !== undefined
  );
  return { analyse: data && data.length > 0 ? data[0] : null, loading, error };
}
