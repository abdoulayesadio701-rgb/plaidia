/**
 * SelecteurLangue.test.tsx — Chantier internationalisation FR/EN : bascule
 * immédiate (sans rechargement), persistance en localStorage, retour au
 * français par défaut.
 */

import { act, render, screen, fireEvent } from "@testing-library/react";
import { useTranslation } from "react-i18next";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import SelecteurLangue from "../SelecteurLangue";
import i18n, { CLE_LANGUE_STOCKEE, definirLangue, langueInitiale } from "@/i18n";

/** Sonde qui affiche un libellé dont la traduction diffère réellement
 * entre fr et en -- pour prouver que le changement de langue se propage
 * immédiatement à tout composant utilisant useTranslation(), sans
 * remontage ni rechargement de page. */
function SondeTraduction() {
  const { t } = useTranslation();
  return <p>{t("commun.annuler")}</p>;
}

describe("SelecteurLangue", () => {
  beforeEach(() => {
    definirLangue("fr");
  });

  afterEach(() => {
    definirLangue("fr");
    try {
      window.localStorage.removeItem(CLE_LANGUE_STOCKEE);
    } catch {
      // ignore
    }
  });

  it("affiche le français comme langue active par défaut", () => {
    render(<SelecteurLangue />);
    expect(screen.getByRole("button", { name: "FR" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute("aria-pressed", "false");
  });

  it("bascule immédiatement vers l'anglais au clic, sans rechargement de page", async () => {
    render(
      <>
        <SelecteurLangue />
        <SondeTraduction />
      </>
    );
    expect(screen.getByText("Annuler")).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "EN" }));
    });

    expect(i18n.language).toBe("en");
    expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute("aria-pressed", "true");
    // Le même rendu (pas de remontage, pas de rechargement) reflète déjà la nouvelle langue.
    expect(screen.getByText("Cancel")).toBeInTheDocument();
    expect(screen.queryByText("Annuler")).not.toBeInTheDocument();
  });

  it("persiste le choix en localStorage", async () => {
    render(<SelecteurLangue />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "EN" }));
    });
    expect(window.localStorage.getItem(CLE_LANGUE_STOCKEE)).toBe("en");

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "FR" }));
    });
    expect(window.localStorage.getItem(CLE_LANGUE_STOCKEE)).toBe("fr");
  });

  it("langueInitiale() retombe sur le français sans valeur stockée ou avec une valeur non reconnue", () => {
    window.localStorage.removeItem(CLE_LANGUE_STOCKEE);
    expect(langueInitiale()).toBe("fr");

    window.localStorage.setItem(CLE_LANGUE_STOCKEE, "es");
    expect(langueInitiale()).toBe("fr");
  });

  it("langueInitiale() reprend la langue mémorisée si elle est reconnue", () => {
    window.localStorage.setItem(CLE_LANGUE_STOCKEE, "en");
    expect(langueInitiale()).toBe("en");
  });
});
