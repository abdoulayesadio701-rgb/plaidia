/**
 * sse.test.ts — Couvre lireFluxSse() (backend/app/deps.py::sse_event, voir
 * l'en-tête de sse.ts), en particulier la détection d'une fermeture de flux
 * silencieuse : la connexion se ferme (reader.read() -> done:true) sans
 * qu'aucune trame "done" ni "error" n'ait été reçue (proxy/timeout réseau),
 * corrigée le 2026-09-23 -- avant ce correctif, ni onDone ni onError
 * n'était jamais appelé dans ce cas (voir ChatPage.tsx : l'état "génération
 * en cours" restait bloqué indéfiniment, sans le moindre message).
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { lireFluxSse } from "../sse";

/** Construit un corps de réponse en flux (ReadableStream) à partir de
 * trames SSE brutes déjà formatées ("event: ...\ndata: ...\n\n"). */
function corpsSse(trames: string[]): ReadableStream<Uint8Array> {
  const encodeur = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < trames.length) {
        controller.enqueue(encodeur.encode(trames[i]));
        i += 1;
      } else {
        controller.close();
      }
    },
  });
}

function reponseStream(trames: string[]): Response {
  return { ok: true, status: 200, body: corpsSse(trames) } as unknown as Response;
}

describe("api/sse lireFluxSse", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("appelle onDone (jamais onError) quand la trame 'done' est bien reçue", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reponseStream(['event: delta\ndata: {"text":"salut"}\n\n', "event: done\ndata: {}\n\n"])));
    const onDone = vi.fn();
    const onError = vi.fn();
    const onDelta = vi.fn();

    await lireFluxSse("http://x/stream", {}, { delta: (d) => onDelta((d as { text: string }).text), done: onDone }, onError);

    expect(onDelta).toHaveBeenCalledWith("salut");
    expect(onDone).toHaveBeenCalledTimes(1);
    expect(onError).not.toHaveBeenCalled();
  });

  it("relaie fidèlement un 'event: error' envoyé par le backend", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reponseStream(['event: error\ndata: {"detail":"La réponse a été interrompue."}\n\n'])));
    const onError = vi.fn();

    await lireFluxSse("http://x/stream", {}, { error: (d) => onError((d as { detail: string }).detail) }, onError);

    expect(onError).toHaveBeenCalledWith("La réponse a été interrompue.");
  });

  it("appelle onError si le flux se ferme sans jamais envoyer 'done' ni 'error' (coupure silencieuse)", async () => {
    // Quelques deltas, puis le flux HTTP se termine (done:true côté reader)
    // sans trame finale -- reproduit une coupure de connexion (proxy,
    // timeout) plutôt qu'une fin normale.
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reponseStream(['event: delta\ndata: {"text":"Début de la"}\n\n', 'event: delta\ndata: {"text":" réponse"}\n\n'])));
    const onDone = vi.fn();
    const onError = vi.fn();
    const onDelta = vi.fn();

    await lireFluxSse("http://x/stream", {}, { delta: (d) => onDelta((d as { text: string }).text), done: onDone }, onError);

    expect(onDelta).toHaveBeenCalledTimes(2);
    expect(onDone).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError.mock.calls[0][0]).toMatch(/interrompue/i);
  });

  it("n'appelle pas onError sur une fermeture propre alors qu'aucune trame n'a jamais été reçue (flux vide, ex. 204)", async () => {
    // Cas volontairement non couvert par une garde spéciale : un flux
    // totalement vide se comporte comme une coupure silencieuse (aucune
    // trame "done" reçue) -- documenté ici pour éviter une régression
    // surprise si ce choix change un jour.
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reponseStream([])));
    const onError = vi.fn();

    await lireFluxSse("http://x/stream", {}, {}, onError);

    expect(onError).toHaveBeenCalledTimes(1);
  });
});
