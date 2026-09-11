/**
 * useLazyStream — pendant de useLazyAction pour les actions déclenchées par
 * un clic qui reçoivent leur résultat en streaming SSE plutôt qu'en une
 * seule réponse (chantier "temps de traitement des générations", §2a/§3) :
 * `data` se remplit progressivement (résultat de l'agent principal d'abord,
 * puis la vérification une fois prête), et `etape` porte le libellé de
 * l'étape en cours pour un indicateur de progression pendant l'attente.
 *
 *   const { data, etape, loading, error, executer } = useLazyStream(
 *     (texte, cb, signal) => analyse.streamAnalyserConclusions(texte, dossierId, cb, signal)
 *   );
 *   <Button onClick={() => executer(texte)} loading={loading}>Analyser</Button>
 *   {etape && <EtapePipelineIndicator etape={etape} />}
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { EtapePipeline } from "@/api/analyse";
import type { Verification } from "@/api/types";

interface CallbacksFlux<T> {
  onEtape?: (etape: EtapePipeline) => void;
  onPrincipal?: (patch: Partial<T>) => void;
  onVerification?: (verification: Verification) => void;
  onDocument?: (patch: Partial<T>) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

interface UseLazyStreamState<T, Args extends unknown[]> {
  data: T | null;
  etape: EtapePipeline | null;
  loading: boolean;
  error: string | null;
  executer: (...args: Args) => Promise<void>;
  reinitialiser: () => void;
  definirDonnees: (donnees: T) => void;
}

export function useLazyStream<T extends object, Args extends unknown[] = []>(
  lancer: (...args: [...Args, CallbacksFlux<T>, AbortSignal]) => Promise<void>
): UseLazyStreamState<T, Args> {
  const [data, setData] = useState<T | null>(null);
  const [etape, setEtape] = useState<EtapePipeline | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  // Annule le flux en cours si le composant se démonte pendant la
  // génération (navigation vers une autre page pendant l'attente).
  useEffect(() => () => controllerRef.current?.abort(), []);

  const executer = useCallback(
    async (...args: Args) => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;

      setLoading(true);
      setError(null);
      setData(null);
      setEtape(null);
      let accumulateur = {} as T;
      const appliquerPatch = (patch: Partial<T>) => {
        accumulateur = { ...accumulateur, ...patch };
        setData({ ...accumulateur });
      };

      try {
        await lancer(...args, {
          onEtape: setEtape,
          onPrincipal: appliquerPatch,
          onVerification: (verification) => appliquerPatch({ verification } as unknown as Partial<T>),
          onDocument: appliquerPatch,
          onDone: () => setEtape(null),
          onError: (message) => setError(message),
        }, controller.signal);
      } finally {
        if (controllerRef.current === controller) setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lancer]
  );

  const reinitialiser = useCallback(() => {
    setData(null);
    setError(null);
    setEtape(null);
  }, []);

  return { data, etape, loading, error, executer, reinitialiser, definirDonnees: setData };
}
