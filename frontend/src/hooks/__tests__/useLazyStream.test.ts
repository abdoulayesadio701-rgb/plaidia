/**
 * useLazyStream.test.ts — Chantier "temps de traitement des générations",
 * §2a/§3 : le résultat de l'agent principal doit être disponible (via
 * `data`) avant que la vérification n'arrive, et l'étape en cours (`etape`)
 * doit refléter ce qu'envoie le flux SSE au fil de l'eau.
 */

import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useLazyStream } from "../useLazyStream";
import type { Verification } from "@/api/types";

interface DonneesTest {
  arguments: string[];
  verification?: Verification;
}

function verificationFactice(statutGlobal: string): Verification {
  return { statut_global: statutGlobal as Verification["statut_global"], elements: [], critiques: [], points_a_verifier: [], synthese_utilisateur: "" };
}

describe("useLazyStream", () => {
  it("expose le résultat principal avant la vérification, puis les deux progressivement", async () => {
    let declencherVerification!: () => void;
    let terminerFlux!: () => void;

    const lancer = (
      cb: {
        onEtape?: (e: { etape: string; libelle: string }) => void;
        onPrincipal?: (patch: Partial<DonneesTest>) => void;
        onVerification?: (v: Verification) => void;
        onDone?: () => void;
      }
    ) =>
      new Promise<void>((resolve) => {
        cb.onEtape?.({ etape: "analyse", libelle: "Analyse en cours" });
        cb.onPrincipal?.({ arguments: ["premier argument"] });
        declencherVerification = () => {
          cb.onEtape?.({ etape: "verification", libelle: "Vérification des sources" });
          cb.onVerification?.(verificationFactice("VERIFIE"));
        };
        terminerFlux = () => {
          cb.onDone?.();
          resolve();
        };
      });

    const { result } = renderHook(() => useLazyStream<DonneesTest, []>(lancer));

    act(() => {
      void result.current.executer();
    });

    // Le résultat principal est déjà là -- pas d'attente du trio qualité.
    await waitFor(() => expect(result.current.data?.arguments).toEqual(["premier argument"]));
    expect(result.current.data?.verification).toBeUndefined();
    expect(result.current.etape?.etape).toBe("analyse");
    expect(result.current.loading).toBe(true);

    act(() => declencherVerification());
    await waitFor(() => expect(result.current.data?.verification?.statut_global).toBe("VERIFIE"));
    // Le résultat principal reste affiché, inchangé -- la vérification s'y ajoute, ne le remplace pas.
    expect(result.current.data?.arguments).toEqual(["premier argument"]);

    act(() => terminerFlux());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.etape).toBeNull();
  });

  it("relaie un message d'erreur envoyé par le flux", async () => {
    const lancer = (cb: { onError?: (message: string) => void }) =>
      new Promise<void>((resolve) => {
        cb.onError?.("Erreur simulée.");
        resolve();
      });

    const { result } = renderHook(() => useLazyStream<DonneesTest, []>(lancer));
    await act(async () => {
      await result.current.executer();
    });

    expect(result.current.error).toBe("Erreur simulée.");
    expect(result.current.loading).toBe(false);
  });
});
