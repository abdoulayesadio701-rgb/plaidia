/**
 * AccesGate.test.tsx : la barrière de mot de passe (voir AccesGate.tsx et
 * backend/app/acces.py). fetch est simulé, aucun serveur n'est appelé.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import AccesGate from "../AccesGate";
import { EN_TETE_ACCES, obtenirMotDePasseAcces, definirMotDePasseAcces } from "@/api/accesMotDePasse";

function reponse(status: number, corps?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (n: string) => (n === "content-type" && corps !== undefined ? "application/json" : null) },
    json: () => Promise.resolve(corps),
  } as unknown as Response;
}

/** Serveur simulé : /api/config annonce la protection ; /api/acces/verifier
 * répond 204 seulement avec le bon mot de passe. */
function serveur(protege: boolean, bonMotDePasse = "secret") {
  return vi.fn((url: string, init?: RequestInit) => {
    if (url.endsWith("/api/config")) return Promise.resolve(reponse(200, { demo_mode: false, max_texte_caracteres: 1, dossier_demo_nom: null, acces_protege: protege }));
    if (url.endsWith("/api/acces/verifier")) {
      const envoye = (init?.headers as Record<string, string> | undefined)?.[EN_TETE_ACCES];
      return Promise.resolve(envoye === bonMotDePasse ? reponse(204) : reponse(401, { detail: "Accès protégé" }));
    }
    return Promise.resolve(reponse(404, { detail: "Not Found" }));
  });
}

describe("AccesGate", () => {
  beforeEach(() => definirMotDePasseAcces(null));
  afterEach(() => {
    vi.unstubAllGlobals();
    definirMotDePasseAcces(null);
  });

  it("affiche l'app directement quand le serveur ne demande pas de mot de passe", async () => {
    vi.stubGlobal("fetch", serveur(false));
    render(<AccesGate><p>contenu de l'app</p></AccesGate>);
    expect(await screen.findByText("contenu de l'app")).toBeInTheDocument();
  });

  it("demande le mot de passe quand le serveur est protégé et qu'aucun n'est stocké", async () => {
    vi.stubGlobal("fetch", serveur(true));
    render(<AccesGate><p>contenu de l'app</p></AccesGate>);
    expect(await screen.findByPlaceholderText("Mot de passe d'accès")).toBeInTheDocument();
    expect(screen.queryByText("contenu de l'app")).not.toBeInTheDocument();
  });

  it("refuse un mauvais mot de passe, ne le garde pas, et reste sur le formulaire", async () => {
    vi.stubGlobal("fetch", serveur(true));
    render(<AccesGate><p>contenu de l'app</p></AccesGate>);
    fireEvent.change(await screen.findByPlaceholderText("Mot de passe d'accès"), { target: { value: "faux" } });
    fireEvent.click(screen.getByRole("button", { name: /Entrer/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Mot de passe incorrect.");
    expect(screen.queryByText("contenu de l'app")).not.toBeInTheDocument();
    expect(obtenirMotDePasseAcces()).toBeNull();
  });

  it("accepte le bon mot de passe, le stocke et affiche l'app", async () => {
    vi.stubGlobal("fetch", serveur(true));
    render(<AccesGate><p>contenu de l'app</p></AccesGate>);
    fireEvent.change(await screen.findByPlaceholderText("Mot de passe d'accès"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: /Entrer/ }));
    expect(await screen.findByText("contenu de l'app")).toBeInTheDocument();
    expect(obtenirMotDePasseAcces()).toBe("secret");
  });

  it("ne redemande rien si le bon mot de passe est déjà stocké", async () => {
    definirMotDePasseAcces("secret");
    vi.stubGlobal("fetch", serveur(true));
    render(<AccesGate><p>contenu de l'app</p></AccesGate>);
    expect(await screen.findByText("contenu de l'app")).toBeInTheDocument();
  });

  it("laisse passer si le serveur est injoignable (l'app affichera ses propres erreurs)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("réseau")));
    render(<AccesGate><p>contenu de l'app</p></AccesGate>);
    await waitFor(() => expect(screen.getByText("contenu de l'app")).toBeInTheDocument());
  });
});
