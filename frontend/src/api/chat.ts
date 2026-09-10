/**
 * chat.ts — Client pour /api/chat (backend/app/routers/chat.py).
 *
 * `EventSource` ne supporte que GET ; comme /api/chat/stream est un POST
 * (il faut envoyer tout l'historique), on lit le corps de la réponse comme
 * un flux et on parse les trames SSE "event: ...\ndata: ...\n\n" à la main —
 * format exact documenté dans backend/README.md.
 */

import { apiRequest, BASE_URL } from "./http";
import { obtenirClePersonnelle } from "./cleApiPersonnelle";
import type { ChatContextuelResultat, ConversationDetail, ConversationResume, FeatureChatContextuel, MessageChat, Verification } from "./types";

export interface ChatStreamCallbacks {
  onRechercheDebut?: () => void;
  onRechercheResultat?: (data: { n_articles: number; n_jurisprudence: number }) => void;
  onDelta?: (text: string) => void;
  /** Additif (ARCHITECTURE_MULTI_AGENTS.md §10) -- envoyé seulement si
   * l'agent d'intention a jugé la question suffisamment substantielle pour
   * justifier le trio qualité, juste avant "done". Absent la plupart du
   * temps (question conversationnelle simple). */
  onVerification?: (verification: Verification) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

export interface ChatStreamOptions {
  rechercheLive?: boolean;
  juridiction?: string;
  /** Si fourni, le backend ajoute le contexte du dossier (faits, parties, dernière analyse) — voir backend/app/routers/chat.py. */
  dossierId?: number | null;
  signal?: AbortSignal;
}

export async function streamChat(messages: MessageChat[], options: ChatStreamOptions, callbacks: ChatStreamCallbacks): Promise<void> {
  const { rechercheLive = false, juridiction = "Légifrance (France)", dossierId = null, signal } = options;

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const clePersonnelle = obtenirClePersonnelle();
  if (clePersonnelle) headers["X-Anthropic-Api-Key"] = clePersonnelle;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/api/chat/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify({ messages, recherche_live: rechercheLive, juridiction, dossier_id: dossierId }),
      signal,
    });
  } catch (e) {
    // Une annulation volontaire (AbortController.abort()) ne doit jamais
    // s'afficher comme une erreur de connexion -- c'est le comportement demandé.
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError?.("Impossible de joindre le serveur. Vérifiez que le backend est lancé.");
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
    callbacks.onError?.(message);
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
    switch (eventName) {
      case "recherche_debut":
        callbacks.onRechercheDebut?.();
        break;
      case "recherche_resultat":
        callbacks.onRechercheResultat?.(data as { n_articles: number; n_jurisprudence: number });
        break;
      case "delta":
        callbacks.onDelta?.((data as { text: string }).text);
        break;
      case "verification":
        callbacks.onVerification?.(data as Verification);
        break;
      case "done":
        callbacks.onDone?.();
        break;
      case "error":
        callbacks.onError?.((data as { detail: string }).detail);
        break;
    }
  };

  // Boucle de lecture : un morceau réseau peut contenir 0, 1 ou plusieurs
  // trames "\n\n"-séparées, et une trame peut être coupée entre deux morceaux
  // — d'où le tampon `buffer` qui ne relâche que ce qui est complet.
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
    callbacks.onError?.("La connexion a été interrompue pendant la génération.");
  }
}

// --- Chat contextuel (édition d'un résultat déjà affiché) ---------------
// Voir ARCHITECTURE_CHAT_CONTEXTUEL.md — un seul mécanisme réutilisé par
// toutes les pages de génération. Pas de streaming ici (voir la note dans
// backend/app/routers/chat.py) : la réponse est validée entièrement côté
// serveur avant de pouvoir en renvoyer quoi que ce soit.

export function envoyerMessageContextuel(
  feature: FeatureChatContextuel,
  message: string,
  resultatActuel: unknown,
  historique: MessageChat[] = [],
  dossierId?: number | null
): Promise<ChatContextuelResultat> {
  return apiRequest<ChatContextuelResultat>("/api/chat/contextuel", {
    method: "POST",
    body: {
      feature,
      message,
      resultat_actuel: resultatActuel,
      historique,
      dossier_id: dossierId ?? null,
    },
  });
}

// --- Historique des conversations (sauvegarde façon Claude.ai) -----------

export function listerConversations(): Promise<ConversationResume[]> {
  return apiRequest<ConversationResume[]>("/api/chat/conversations");
}

export function obtenirConversation(id: number): Promise<ConversationDetail> {
  return apiRequest<ConversationDetail>(`/api/chat/conversations/${id}`);
}

export function creerConversation(titre: string, historique: MessageChat[], dossierId?: number | null): Promise<ConversationResume> {
  return apiRequest<ConversationResume>("/api/chat/conversations", {
    method: "POST",
    body: { titre, historique, dossier_id: dossierId ?? null },
  });
}

export function listerConversationsDossier(dossierId: number): Promise<ConversationResume[]> {
  return apiRequest<ConversationResume[]>(`/api/chat/conversations/dossier/${dossierId}`);
}

export function mettreAJourConversation(id: number, historique: MessageChat[]): Promise<ConversationResume> {
  return apiRequest<ConversationResume>(`/api/chat/conversations/${id}`, { method: "PUT", body: { historique } });
}

export function supprimerConversation(id: number): Promise<void> {
  return apiRequest<void>(`/api/chat/conversations/${id}`, { method: "DELETE" });
}
