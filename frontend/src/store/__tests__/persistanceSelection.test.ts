import { beforeEach, describe, expect, it, vi } from "vitest";

const listerDossiersMock = vi.fn();

vi.mock("@/api/dossiers", () => ({
  listerDossiers: (...args: unknown[]) => listerDossiersMock(...args),
}));

function dossier(id: number) {
  return { id, nom: `Dossier ${id}`, statut: "en cours", date_creation: "2026-01-01" };
}

// Le store lit localStorage à l'import : on le réimporte à neuf à chaque test.
async function importerStore() {
  vi.resetModules();
  return (await import("../useAppStore")).useAppStore;
}

describe("persistance du dossier et de l'espace actifs", () => {
  beforeEach(() => {
    localStorage.clear();
    listerDossiersMock.mockReset();
  });

  it("sélectionner un dossier l'écrit, le désélectionner l'efface", async () => {
    const store = await importerStore();
    store.getState().selectionnerDossier(5);
    expect(localStorage.getItem("plaidia:dossier-actif")).toBe("5");
    store.getState().selectionnerDossier(null);
    expect(localStorage.getItem("plaidia:dossier-actif")).toBeNull();
  });

  it("restaure le dossier mémorisé au démarrage", async () => {
    localStorage.setItem("plaidia:dossier-actif", "7");
    const store = await importerStore();
    expect(store.getState().dossierActifId).toBe(7);
  });

  it("garde le dossier mémorisé s'il existe encore après chargement de la liste", async () => {
    localStorage.setItem("plaidia:dossier-actif", "7");
    listerDossiersMock.mockResolvedValue([dossier(3), dossier(7)]);
    const store = await importerStore();
    await store.getState().chargerDossiers();
    expect(store.getState().dossierActifId).toBe(7);
    expect(localStorage.getItem("plaidia:dossier-actif")).toBe("7");
  });

  it("oublie le dossier mémorisé s'il n'existe plus", async () => {
    localStorage.setItem("plaidia:dossier-actif", "7");
    listerDossiersMock.mockResolvedValue([dossier(3)]);
    const store = await importerStore();
    await store.getState().chargerDossiers();
    expect(store.getState().dossierActifId).toBeNull();
    expect(localStorage.getItem("plaidia:dossier-actif")).toBeNull();
  });

  it("ignore une valeur mémorisée invalide", async () => {
    localStorage.setItem("plaidia:dossier-actif", "abc");
    const store = await importerStore();
    expect(store.getState().dossierActifId).toBeNull();
  });

  it("retirer le dossier actif efface la mémoire", async () => {
    localStorage.setItem("plaidia:dossier-actif", "7");
    const store = await importerStore();
    store.getState().retirerDossierLocal(7);
    expect(localStorage.getItem("plaidia:dossier-actif")).toBeNull();
  });

  it("l'espace choisi survit au rechargement", async () => {
    const premier = await importerStore();
    expect(premier.getState().espaceActif).toBe("avocat");
    premier.getState().definirEspace("greffier");
    const second = await importerStore();
    expect(second.getState().espaceActif).toBe("greffier");
  });
});
