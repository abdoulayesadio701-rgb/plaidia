/**
 * veille.ts — Client typé pour /api/veille (backend/app/routers/veille.py)
 * -- portage web de gui.py::DialogueNotificationsVeille / DialogueAlertesArticles.
 */

import { apiRequest } from "./http";
import type { NotificationsVeille } from "./types";

export function notifications(dossierId?: number): Promise<NotificationsVeille> {
  return apiRequest<NotificationsVeille>("/api/veille/notifications", { query: { dossier_id: dossierId } });
}

/** Déclenche un passage de veille immédiat plutôt que d'attendre la
 * prochaine itération de la boucle horaire côté serveur. Sans effet en
 * mode démo (voir backend/app/veille.py::executer_un_passage). */
export function declencherVerification(): Promise<void> {
  return apiRequest<void>("/api/veille/verifier", { method: "POST" });
}

export function acquitterJurisprudence(id: number): Promise<void> {
  return apiRequest<void>(`/api/veille/jurisprudence/${id}/acquitter`, { method: "POST" });
}

export function acquitterLoi(id: number): Promise<void> {
  return apiRequest<void>(`/api/veille/lois/${id}/acquitter`, { method: "POST" });
}

export function marquerOhadaVerifie(): Promise<void> {
  return apiRequest<void>("/api/veille/ohada/marquer-verifie", { method: "POST" });
}
