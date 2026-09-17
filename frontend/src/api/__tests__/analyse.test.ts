/**
 * analyse.test.ts — Garde-fou minimal sur la couche API de /api/analyse
 * (backend/app/routers/analyse.py) pour les fonctionnalités "cycle de vie
 * des documents" (statuts) et "persistance des plans/simulateurs" : vérifie
 * que chaque fonction appelle la bonne URL/méthode/corps et relaie
 * fidèlement la réponse. Ne couvre pas le branchement dans les pages
 * (AnalyserConclusionsPage, PlanPlaidoiriePage, SimulateurObjectionsPage) --
 * volontairement, pour rester un test minimal côté API.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { changerStatutDocument, genererPlan, simulerObjections } from "../analyse";
import type { DocumentGenere, PlanResultat, SimulateurResultat } from "../types";

function reponseJson(corps: unknown): Response {
  return {
    ok: true,
    status: 200,
    headers: { get: (nom: string) => (nom === "content-type" ? "application/json" : null) },
    json: () => Promise.resolve(corps),
  } as unknown as Response;
}

describe("api/analyse", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("changerStatutDocument envoie un PATCH vers /api/documents-generes/{id}/statut avec le nouveau statut", async () => {
    const documentMaj: DocumentGenere = {
      id: 7,
      dossier_id: 3,
      feature: "plan",
      titre: "Plan de plaidoirie",
      parametres: {},
      contenu: {},
      statut: "Validé",
      date_creation: "2026-09-10T10:00:00Z",
      date_modification: "2026-09-17T10:00:00Z",
    };
    const fetchMock = vi.fn().mockResolvedValue(reponseJson(documentMaj));
    vi.stubGlobal("fetch", fetchMock);

    const resultat = await changerStatutDocument(7, "Validé");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/documents-generes/7/statut");
    expect(options.method).toBe("PATCH");
    expect(JSON.parse(options.body)).toEqual({ statut: "Validé" });
    expect(resultat).toEqual(documentMaj);
  });

  it("genererPlan envoie dossier_id et temps_minutes vers /api/analyse/plan", async () => {
    const plan: PlanResultat = { accroche: "Accroche", plan: [], conclusion: "Conclusion", points_attention: [] };
    const fetchMock = vi.fn().mockResolvedValue(reponseJson(plan));
    vi.stubGlobal("fetch", fetchMock);

    const resultat = await genererPlan(3, 10);

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/analyse/plan");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual({ dossier_id: 3, temps_minutes: 10 });
    expect(resultat).toEqual(plan);
  });

  it("simulerObjections envoie le dossier_id vers /api/analyse/simulateur", async () => {
    const simulateur: SimulateurResultat = { objections: [], point_le_plus_faible: "Absence de témoin direct." };
    const fetchMock = vi.fn().mockResolvedValue(reponseJson(simulateur));
    vi.stubGlobal("fetch", fetchMock);

    const resultat = await simulerObjections(3);

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/analyse/simulateur");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual({ dossier_id: 3 });
    expect(resultat).toEqual(simulateur);
  });
});
