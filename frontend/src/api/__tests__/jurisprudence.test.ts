/**
 * jurisprudence.test.ts — Garde-fou minimal sur la couche API de
 * /api/jurisprudence (backend/app/routers/jurisprudence.py) pour la
 * fonctionnalité "persistance des consultations" : vérifie que
 * consulterJurisprudence() envoie bien le dossier_id (c'est lui qui
 * rattache la consultation au dossier, voir ConsulterJurisprudencePage.tsx)
 * et relaie fidèlement la réponse.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { consulterJurisprudence } from "../jurisprudence";
import type { ConsulterResultat } from "../types";

function reponseJson(corps: unknown): Response {
  return {
    ok: true,
    status: 200,
    headers: { get: (nom: string) => (nom === "content-type" ? "application/json" : null) },
    json: () => Promise.resolve(corps),
  } as unknown as Response;
}

describe("api/jurisprudence", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("consulterJurisprudence envoie question, but, source et dossier_id vers /api/jurisprudence/consulter", async () => {
    const consultation: ConsulterResultat = {
      notions: { domaine: "Social", qualification_juridique: "Licenciement", mots_cles_recherche: ["licenciement"], but: "décisions favorables" },
      reponse: "Réponse.",
    };
    const fetchMock = vi.fn().mockResolvedValue(reponseJson(consultation));
    vi.stubGlobal("fetch", fetchMock);

    const resultat = await consulterJurisprudence("Un salarié peut-il...", "décisions favorables", "Légifrance (France)", 3);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/jurisprudence/consulter");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual({
      question: "Un salarié peut-il...",
      but: "décisions favorables",
      source: "Légifrance (France)",
      dossier_id: 3,
    });
    expect(resultat).toEqual(consultation);
  });
});
