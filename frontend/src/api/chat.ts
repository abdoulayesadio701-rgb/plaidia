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
import { entetesSse, lireFluxSse } from "./sse";
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

  const headers = entetesSse();
  const clePersonnelle = obtenirClePersonnelle();
  if (clePersonnelle) headers["X-Anthropic-Api-Key"] = clePersonnelle;

  await lireFluxSse(
    `${BASE_URL}/api/chat/stream`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ messages, recherche_live: rechercheLive, juridiction, dossier_id: dossierId }),
      signal,
    },
    {
      recherche_debut: () => callbacks.onRechercheDebut?.(),
      recherche_resultat: (data) => callbacks.onRechercheResultat?.(data as { n_articles: number; n_jurisprudence: number }),
      delta: (data) => callbacks.onDelta?.((data as { text: string }).text),
      verification: (data) => callbacks.onVerification?.(data as Verification),
      done: () => callbacks.onDone?.(),
      error: (data) => callbacks.onError?.((data as { detail: string }).detail),
    },
    callbacks.onError
  );
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
  dossierId?: number | null,
  documentId?: number | null
): Promise<ChatContextuelResultat> {
  return apiRequest<ChatContextuelResultat>("/api/chat/contextuel", {
    method: "POST",
    body: {
      feature,
      message,
      resultat_actuel: resultatActuel,
      historique,
      dossier_id: dossierId ?? null,
      document_id: documentId ?? null,
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
