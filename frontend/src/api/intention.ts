/**
 * intention.ts — Client typé pour /api/intention (backend/app/routers/intention.py).
 */

import { apiRequest } from "./http";
import type { Intention } from "./types";

export function interpreterIntention(texte: string): Promise<Intention> {
  return apiRequest<Intention>("/api/intention/interpreter", { method: "POST", body: { texte } });
}
