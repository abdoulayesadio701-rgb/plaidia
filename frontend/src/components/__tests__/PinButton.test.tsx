import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import PinButton from "../PinButton";

const epinglerElement = vi.fn();
const desepinglerElement = vi.fn();

vi.mock("@/store/useAppStore", () => ({
  useIdEpingle: () => null,
  useAppStore: (selecteur: (etat: unknown) => unknown) =>
    selecteur({ epinglerElement, desepinglerElement }),
}));

describe("PinButton", () => {
  it("épingle un document généré au clic", () => {
    render(<PinButton type="document_genere" referenceId={12} dossierId={3} libelle="Plan" />);

    fireEvent.click(screen.getByRole("button", { name: /Épingler/ }));

    expect(epinglerElement).toHaveBeenCalledWith("document_genere", 12, "Plan", 3);
  });
});
