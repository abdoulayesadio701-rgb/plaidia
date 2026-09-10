import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useImportTexte } from "../useImportTexte";

const extraireFichierMock = vi.fn();
const importerDocumentMock = vi.fn();

vi.mock("@/api/dossiers", () => ({
  extraireFichier: (...args: unknown[]) => extraireFichierMock(...args),
  importerDocument: (...args: unknown[]) => importerDocumentMock(...args),
}));

function fichier(nom: string): File {
  return new File(["contenu"], nom, { type: "text/plain" });
}

function resultatExtrait(nom: string, texte: string) {
  return { nom_fichier: nom, texte_extrait: texte, caracteres_extraits: texte.length };
}

describe("useImportTexte", () => {
  beforeEach(() => {
    extraireFichierMock.mockReset();
    importerDocumentMock.mockReset();
  });

  it("injecte directement le texte extrait quand le champ est vide (pas de choix demandé)", async () => {
    extraireFichierMock.mockResolvedValue(resultatExtrait("conclusions.pdf", "Texte extrait"));
    let texte = "";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: null, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("conclusions.pdf")]);
    });

    expect(texte).toBe("Texte extrait");
    expect(result.current.choixEnAttente).toBeNull();
    expect(extraireFichierMock).toHaveBeenCalledTimes(1);
  });

  it("utilise importerDocument (pas extraireFichier) quand un dossierId est fourni", async () => {
    importerDocumentMock.mockResolvedValue(resultatExtrait("piece.pdf", "Contenu"));
    let texte = "";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: 42, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("piece.pdf")]);
    });

    expect(importerDocumentMock).toHaveBeenCalledWith(42, expect.anything());
    expect(extraireFichierMock).not.toHaveBeenCalled();
    expect(texte).toBe("Contenu");
  });

  it("concatène plusieurs fichiers avec un séparateur qui nomme chacun", async () => {
    extraireFichierMock.mockImplementation((f: File) => Promise.resolve(resultatExtrait(f.name, `contenu de ${f.name}`)));
    let texte = "";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: null, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("a.pdf"), fichier("b.docx")]);
    });

    expect(texte).toContain("--- a.pdf ---");
    expect(texte).toContain("contenu de a.pdf");
    expect(texte).toContain("--- b.docx ---");
    expect(texte).toContain("contenu de b.docx");
  });

  it("demande de choisir remplacer/ajouter quand le champ contient déjà du texte, sans l'écraser avant la décision", async () => {
    extraireFichierMock.mockResolvedValue(resultatExtrait("nouveau.pdf", "Nouveau contenu"));
    let texte = "Texte déjà présent";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: null, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("nouveau.pdf")]);
    });

    expect(texte).toBe("Texte déjà présent");
    expect(result.current.choixEnAttente).toEqual({ texte: "Nouveau contenu", noms: ["nouveau.pdf"] });

    act(() => {
      result.current.resoudreChoix("ajouter");
    });
    expect(texte).toBe("Texte déjà présent\n\nNouveau contenu");
    expect(result.current.choixEnAttente).toBeNull();
  });

  it("remplace le texte existant quand l'utilisateur choisit « remplacer »", async () => {
    extraireFichierMock.mockResolvedValue(resultatExtrait("nouveau.pdf", "Nouveau contenu"));
    let texte = "Ancien texte";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: null, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("nouveau.pdf")]);
    });
    act(() => {
      result.current.resoudreChoix("remplacer");
    });

    expect(texte).toBe("Nouveau contenu");
  });

  it("annuler laisse le texte existant intact", async () => {
    extraireFichierMock.mockResolvedValue(resultatExtrait("nouveau.pdf", "Nouveau contenu"));
    let texte = "Ancien texte";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: null, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("nouveau.pdf")]);
    });
    act(() => {
      result.current.resoudreChoix("annuler");
    });

    expect(texte).toBe("Ancien texte");
    expect(result.current.choixEnAttente).toBeNull();
  });

  it("un fichier en échec n'empêche pas l'import des autres fichiers du même lot", async () => {
    extraireFichierMock.mockImplementation((f: File) =>
      f.name === "corrompu.pdf"
        ? Promise.reject(new Error("Impossible de lire ce fichier : il semble corrompu."))
        : Promise.resolve(resultatExtrait(f.name, "contenu valide"))
    );
    let texte = "";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: null, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("corrompu.pdf"), fichier("valide.pdf")]);
    });

    expect(texte).toBe("contenu valide");
    expect(result.current.enImport).toBe(false);
  });

  it("ne casse pas et ne modifie rien si tous les fichiers du lot échouent", async () => {
    extraireFichierMock.mockRejectedValue(new Error("Format non supporté."));
    let texte = "";
    const { result } = renderHook(() =>
      useImportTexte({ dossierId: null, getTexteActuel: () => texte, onTexteExtrait: (t) => (texte = t) })
    );

    await act(async () => {
      await result.current.importerFichiers([fichier("inconnu.xyz")]);
    });

    expect(texte).toBe("");
    expect(result.current.choixEnAttente).toBeNull();
    expect(result.current.enImport).toBe(false);
  });
});
