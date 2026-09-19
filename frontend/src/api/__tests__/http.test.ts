import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "../http";

function reponseErreur(status: number, corps: unknown): Response {
  return {
    ok: false,
    status,
    headers: { get: (nom: string) => (nom === "content-type" ? "application/json" : null) },
    json: () => Promise.resolve(corps),
  } as unknown as Response;
}

async function erreurDe(status: number, corps: unknown): Promise<ApiError> {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reponseErreur(status, corps)));
  try {
    await apiRequest("/api/quelque-chose");
  } catch (e) {
    return e as ApiError;
  }
  throw new Error("aucune erreur levée");
}

describe("messages d'erreur de l'API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("un « Not Found » nu (route absente) signale un serveur plus ancien que l'interface", async () => {
    const erreur = await erreurDe(404, { detail: "Not Found" });
    expect(erreur.status).toBe(404);
    expect(erreur.message).toContain("plus ancienne");
  });

  it("un 404 métier garde son propre message", async () => {
    const erreur = await erreurDe(404, { detail: "Dossier 12 introuvable." });
    expect(erreur.message).toBe("Dossier 12 introuvable.");
  });

  it("un 500 avec message le garde aussi", async () => {
    expect((await erreurDe(500, { detail: "Erreur de configuration serveur" })).message).toBe("Erreur de configuration serveur");
  });
});
