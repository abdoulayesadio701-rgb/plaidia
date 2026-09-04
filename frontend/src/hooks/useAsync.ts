/**
 * useAsync — standardise le triptyque chargement / erreur / données que
 * chaque page d'action devra gérer (voir consigne "Gestion du chargement
 * et des erreurs sur chaque page"). Les futures pages n'ont qu'à faire :
 *
 *   const { data, loading, error, reload } = useAsync(
 *     () => analyse.resumerDossier(dossierId), [dossierId]
 *   );
 *   if (loading) return <Spinner message="Résumé en cours…" />;
 *   if (error) return <ErrorState message={error} onRetry={reload} />;
 *   return <RichOutput texte={data.resume_court} />;
 *
 * N'exécute rien tant que `enabled` est faux (ex. pas encore de dossier
 * actif) — évite un appel API avec des paramètres invalides.
 */

import { useCallback, useEffect, useState, type DependencyList } from "react";

interface UseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useAsync<T>(fn: () => Promise<T>, deps: DependencyList, enabled = true): UseAsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);
  const [tentative, setTentative] = useState(0);

  const reload = useCallback(() => setTentative((t) => t + 1), []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    let annule = false;
    setLoading(true);
    setError(null);
    fn()
      .then((resultat) => {
        if (!annule) setData(resultat);
      })
      .catch((e: unknown) => {
        if (!annule) setError(e instanceof Error ? e.message : "Une erreur est survenue.");
      })
      .finally(() => {
        if (!annule) setLoading(false);
      });
    return () => {
      annule = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, enabled, tentative]);

  return { data, loading, error, reload };
}
