import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import StatutDocumentMenu, { statutsAutorises } from "../StatutDocument";

describe("StatutDocument", () => {
  it("propose uniquement les voisins autorisés", () => {
    expect(statutsAutorises("En révision")).toEqual(["En cours", "Validé"]);
  });

  it("ne propose aucune transition depuis Final", () => {
    render(<StatutDocumentMenu statut="Final" onChange={() => undefined} />);
    expect(screen.queryByRole("combobox")).toBeNull();
  });
});
