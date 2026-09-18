import { describe, expect, it } from "vitest";
import { NAVIGATION } from "../navigation";
import { ROUTES_PAR_ACTION } from "../intentions";

describe("ROUTES_PAR_ACTION", () => {
  const cheminsConnus = new Set(
    Object.values(NAVIGATION).flatMap((sections) => sections.flatMap((section) => section.items.map((item) => item.path)))
  );

  it("chaque action mène à une page réellement présente dans la navigation", () => {
    for (const [action, chemin] of Object.entries(ROUTES_PAR_ACTION)) {
      expect(cheminsConnus.has(chemin), `${action} -> ${chemin}`).toBe(true);
    }
  });

  it("reconnaît les fonctionnalités récentes", () => {
    for (const action of ["chronologie", "verification", "delais", "entrainement", "bordereau"]) {
      expect(ROUTES_PAR_ACTION[action]).toBeDefined();
    }
  });
});
