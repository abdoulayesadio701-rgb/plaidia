/**
 * sse.ts — Lecture générique d'un flux Server-Sent Events envoyé par un
 * endpoint POST du backend (voir backend/app/deps.py::sse_event -- format
 * "event: ...\ndata: ...\n\n" documenté dans backend/README.md).
 *
 * `EventSource` ne supporte que GET ; ces endpoints sont des POST (il faut
 * envoyer un corps JSON), donc on lit le corps de la réponse comme un flux
 * et on parse les trames à la main -- extrait de frontend/src/api/chat.ts
 * (streamChat), pour être réutilisé par tout endpoint en streaming
 * (chantier "temps de traitement des générations", §2a).
 */

import i18nInstance from "@/i18n";

export type GestionnairesSse = Record<string, (data: unknown) => void>;

/** En-têtes communs à toute requête SSE : la langue choisie (voir
 * frontend/src/api/http.ts::doFetch, même principe) -- ces appels ne
 * passent pas par doFetch (ils ont besoin de response.body en flux), donc
 * l'en-tête est ajouté ici plutôt qu'oublié. */
export function entetesSse(extra?: Record<string, string>): Record<string, string> {
  return { "Content-Type": "application/json", "X-Langue": i18nInstance.language || "fr", ...extra };
}

export async function lireFluxSse(
  url: string,
  init: RequestInit,
  gestionnaires: GestionnairesSse,
  onError?: (message: string) => void
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (e) {
    // Une annulation volontaire (AbortController.abort()) ne doit jamais
    // s'afficher comme une erreur de connexion.
    if (e instanceof DOMException && e.name === "AbortError") return;
    onError?.("Impossible de joindre le serveur. Vérifiez que le backend est lancé.");
    return;
  }

  if (!response.ok || !response.body) {
    let message = `Erreur ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") message = data.detail;
    } catch {
      /* pas de corps JSON exploitable */
    }
    onError?.(message);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  const dispatch = (rawEvent: string) => {
    let eventName = "message";
    let dataLine = "";
    for (const line of rawEvent.split("\n")) {
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLine += line.slice(5).trim();
    }
    if (!dataLine) return;
    let data: unknown;
    try {
      data = JSON.parse(dataLine);
    } catch {
      return;
    }
    gestionnaires[eventName]?.(data);
  };

  // Boucle de lecture : un morceau réseau peut contenir 0, 1 ou plusieurs
  // trames "\n\n"-séparées, et une trame peut être coupée entre deux
  // morceaux — d'où le tampon `buffer` qui ne relâche que ce qui est complet.
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sepIndex: number;
      while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        if (rawEvent.trim()) dispatch(rawEvent);
      }
    }
  } catch (e) {
    // Annulation volontaire en cours de flux (bouton "Arrêter la génération")
    // -- silencieuse, ce n'est pas une erreur à afficher.
    if (e instanceof DOMException && e.name === "AbortError") return;
    onError?.("La connexion a été interrompue pendant la génération.");
  }
}
