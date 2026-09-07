/**
 * useLazyAction — pendant de useAsync pour les actions déclenchées par un
 * clic plutôt qu'au chargement de la page. Toutes les pages de L'Arsenal
 * appellent l'API Claude côté serveur (coût réel, latence réelle) : ne
 * JAMAIS déclencher ça automatiquement à la navigation, seulement sur une
 * action explicite de l'avocat — d'où ce hook plutôt que useAsync partout.
 *
 *   const { data, loading, error, executer, reinitialiser } = useLazyAction(
 *     (texte: string) => analyse.analyserConclusions(texte, dossierId)
 *   );
 *   <Button onClick={() => executer(texte)} loading={loading}>Analyser</Button>
 *   {error && <ErrorState message={error} onRetry={() => executer(texte)} />}
 */

import { useCallback, useState } from "react";

interface UseLazyActionState<T, Args extends unknown[]> {
  data: T | null;
  loading: boolean;
  error: string | null;
  executer: (...args: Args) => Promise<T | undefined>;
  reinitialiser: () => void;
  /** Remplace `data` sans repasser par `fn` — utilisé par ChatContextuelPanel
   * pour appliquer un résultat déjà corrigé côté serveur (voir
   * ARCHITECTURE_CHAT_CONTEXTUEL.md §2.5) sans relancer toute la génération. */
  definirDonnees: (donnees: T) => void;
}

export function useLazyAction<T, Args extends unknown[] = []>(fn: (...args: Args) => Promise<T>): UseLazyActionState<T, Args> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executer = useCallback(
    async (...args: Args) => {
      setLoading(true);
      setError(null);
      try {
        const resultat = await fn(...args);
        setData(resultat);
        return resultat;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Une erreur est survenue.");
        return undefined;
      } finally {
        setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fn]
  );

  const reinitialiser = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, executer, reinitialiser, definirDonnees: setData };
}
