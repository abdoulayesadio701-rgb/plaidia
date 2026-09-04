/**
 * http.ts — Client HTTP de base pour l'API Plaid'IA (backend/).
 *
 * Toute erreur backend revient en JSON {"detail": ...} (voir
 * backend/app/main.py) — traduite ici en ApiError avec un message déjà
 * exploitable tel quel dans l'UI (toast, état d'erreur de page...).
 */

import { useActivityStore } from "@/store/useActivityStore";
import { obtenirClePersonnelle } from "./cleApiPersonnelle";

const BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

type Query = Record<string, string | number | boolean | undefined | null>;

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Query;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: Query): string {
  let url = `${BASE_URL}${path}`;
  if (query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) params.set(key, String(value));
    }
    const qs = params.toString();
    if (qs) url += (path.includes("?") ? "&" : "?") + qs;
  }
  return url;
}

/** Extrait un message lisible du corps {"detail": ...} renvoyé par FastAPI
 * — soit une chaîne (nos exception handlers), soit la liste d'erreurs de
 * validation Pydantic ({"detail": [{"msg": ..., "loc": [...]}]}). */
function messageFromDetail(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : null))
      .filter((m): m is string => Boolean(m));
    if (messages.length) return messages.join(" ; ");
  }
  return `Erreur ${status}`;
}

async function parseErrorBody(response: Response): Promise<{ detail: unknown; message: string }> {
  try {
    const data = await response.json();
    const detail = data?.detail ?? data;
    return { detail, message: messageFromDetail(detail, response.status) };
  } catch {
    return { detail: null, message: `Erreur ${response.status}` };
  }
}

async function withActivity<T>(fn: () => Promise<T>): Promise<T> {
  useActivityStore.getState().demarrer();
  try {
    return await fn();
  } finally {
    useActivityStore.getState().terminer();
  }
}

async function doFetch(path: string, options: RequestOptions, extraHeaders?: HeadersInit, rawBody?: BodyInit): Promise<Response> {
  const { method = "GET", body, query, signal } = options;
  const url = buildUrl(path, query);
  const headers: HeadersInit = { ...extraHeaders };
  let finalBody: BodyInit | undefined = rawBody;
  if (rawBody === undefined && body !== undefined) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
    finalBody = JSON.stringify(body);
  }
  // "Utiliser ma propre clé Anthropic" (voir cleApiPersonnelle.ts) --
  // attachée automatiquement à toute requête si présente en sessionStorage,
  // jamais journalisée. Le serveur la lit via un middleware et ne l'écrit
  // jamais sur disque (voir backend/app/main.py).
  const clePersonnelle = obtenirClePersonnelle();
  if (clePersonnelle) (headers as Record<string, string>)["X-Anthropic-Api-Key"] = clePersonnelle;
  try {
    return await fetch(url, { method, headers, body: finalBody, signal });
  } catch {
    throw new ApiError(0, null, "Impossible de joindre le serveur. Vérifiez que le backend est lancé (voir backend/README.md).");
  }
}

/** Requête JSON standard. Lève une ApiError avec un message déjà lisible en cas d'échec. */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return withActivity(async () => {
    const response = await doFetch(path, options);
    if (!response.ok) {
      const { detail, message } = await parseErrorBody(response);
      throw new ApiError(response.status, detail, message);
    }
    if (response.status === 204) return undefined as T;
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) return (await response.json()) as T;
    return undefined as T;
  });
}

/** Upload multipart (import de document). `formData` doit déjà contenir le(s) champ(s) attendu(s). */
export async function apiUpload<T>(path: string, formData: FormData, query?: Query, signal?: AbortSignal): Promise<T> {
  return withActivity(async () => {
    const response = await doFetch(path, { method: "POST", query, signal }, undefined, formData);
    if (!response.ok) {
      const { detail, message } = await parseErrorBody(response);
      throw new ApiError(response.status, detail, message);
    }
    return (await response.json()) as T;
  });
}

function filenameFromContentDisposition(header: string | null): string | undefined {
  if (!header) return undefined;
  const match = header.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
  return match ? decodeURIComponent(match[1]) : undefined;
}

/** Requête dont la réponse est un fichier (export Word/PDF). */
export async function apiRequestBlob(
  path: string,
  options: RequestOptions = {}
): Promise<{ blob: Blob; filename?: string }> {
  return withActivity(async () => {
    const response = await doFetch(path, options);
    if (!response.ok) {
      const { detail, message } = await parseErrorBody(response);
      throw new ApiError(response.status, detail, message);
    }
    const blob = await response.blob();
    const filename = filenameFromContentDisposition(response.headers.get("content-disposition"));
    return { blob, filename };
  });
}

/** Déclenche le téléchargement d'un blob côté navigateur (export Word/PDF). */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export { BASE_URL };
