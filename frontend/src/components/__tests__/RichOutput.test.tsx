/**
 * RichOutput.test.tsx — Couvre le garde-fou anti-hallucination visuel
 * (surlignage du marqueur "À VÉRIFIER") et le strict minimum du rendu
 * markdown léger (gras, titres, listes) que RichOutput doit produire.
 *
 * Le test le plus important ici est `ne surligne pas un marqueur encore
 * incomplet` : c'est la propriété documentée dans RichOutput.tsx qui rend
 * le composant robuste au streaming SSE (le marqueur peut être coupé entre
 * deux fragments "delta" -- voir backend/app/routers/chat.py). Un
 * changement qui casserait cette robustesse (ex. un surlignage qui
 * réagirait à un préfixe partiel) doit faire échouer ce test.
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import RichOutput from "../RichOutput";

describe("RichOutput", () => {
  it("surligne le marqueur À VÉRIFIER dans un <mark> dédié", () => {
    render(<RichOutput texte="Ceci est À VÉRIFIER avant toute utilisation." />);

    const marqueur = screen.getByText("À VÉRIFIER");
    expect(marqueur.tagName).toBe("MARK");
    expect(marqueur).toHaveClass("marker-verify");
  });

  it("ne surligne pas un marqueur encore incomplet (robustesse au streaming SSE)", () => {
    const { container, rerender } = render(<RichOutput texte="Le texte accumulé jusqu'ici dit : À VÉRI" />);

    // Le marqueur est coupé en plein milieu -- aucun <mark> ne doit encore
    // exister, et le texte partiel doit rester visible tel quel (pas de
    // sous-chaîne discrètement avalée par le parseur).
    expect(container.querySelector("mark")).toBeNull();
    expect(container.textContent).toContain("À VÉRI");

    // Le fragment SSE suivant arrive : le marqueur est maintenant complet.
    rerender(<RichOutput texte="Le texte accumulé jusqu'ici dit : À VÉRIFIER avant usage." />);

    const marqueur = screen.getByText("À VÉRIFIER");
    expect(marqueur.tagName).toBe("MARK");
    expect(marqueur).toHaveClass("marker-verify");
  });

  it("rend le gras **...** en <strong>", () => {
    render(<RichOutput texte="Un point **vraiment important** à retenir." />);
    const fort = screen.getByText("vraiment important");
    expect(fort.tagName).toBe("STRONG");
  });

  it("rend un titre markdown (#) avec la bonne balise", () => {
    render(<RichOutput texte="# Titre principal" />);
    expect(screen.getByRole("heading", { level: 1, name: "Titre principal" })).toBeInTheDocument();
  });

  it("rend une liste à puces en <ul><li>", () => {
    render(<RichOutput texte={"- premier point\n- second point"} />);
    const liste = screen.getByRole("list");
    expect(liste.tagName).toBe("UL");
    // getByText peut retourner le <span> interne porteur du texte plutôt
    // que le <li> lui-même (RichOutput enveloppe chaque item) -- on
    // vérifie l'ancêtre <li> plutôt que le tagName direct.
    expect(screen.getByText("premier point").closest("li")).not.toBeNull();
    expect(screen.getByText("second point").closest("li")).not.toBeNull();
    expect(liste.querySelectorAll("li")).toHaveLength(2);
  });

  it("gère un marqueur au tout début et à la toute fin d'un texte", () => {
    render(<RichOutput texte="À VÉRIFIER : relire ce point À VÉRIFIER" prose={false} />);
    const marqueurs = screen.getAllByText("À VÉRIFIER");
    expect(marqueurs).toHaveLength(2);
    marqueurs.forEach((m) => expect(m.tagName).toBe("MARK"));
  });

  it("rend une balise [ART:...] en citation lisible", () => {
    render(<RichOutput texte="Le principe [ART:132-24:CP] impose au juge de tenir compte des éléments." />);
    const citation = screen.getByText("art. 132-24 du Code pénal");
    expect(citation.tagName).toBe("SPAN");
    expect(citation).toHaveClass("marker-citation");
  });

  it("rend une balise [JURISPRUDENCE:...] en citation lisible", () => {
    render(<RichOutput texte="[JURISPRUDENCE:Cass. Crim., 12 mars 2023, n°22-84.123] le confirme." />);
    const citation = screen.getByText("Cass. Crim., 12 mars 2023, n°22-84.123");
    expect(citation.tagName).toBe("SPAN");
    expect(citation).toHaveClass("marker-citation");
  });

  it("rend une balise [VERIF:...] comme l'ancien marqueur À VÉRIFIER", () => {
    render(<RichOutput texte="Un point [VERIF:absence de rapport d'enquête] reste incertain." />);
    const marqueur = screen.getByText("À VÉRIFIER : absence de rapport d'enquête");
    expect(marqueur.tagName).toBe("MARK");
    expect(marqueur).toHaveClass("marker-verify");
  });

  it("ne rend pas une balise [VERIF:...] encore incomplète (robustesse au streaming SSE)", () => {
    const { container, rerender } = render(<RichOutput texte="Un point [VERIF:absence de rap" />);

    // La balise n'est pas fermée -- aucun <mark> ne doit encore exister.
    expect(container.querySelector("mark")).toBeNull();
    expect(container.textContent).toContain("[VERIF:absence de rap");

    rerender(<RichOutput texte="Un point [VERIF:absence de rapport] reste incertain." />);
    const marqueur = screen.getByText("À VÉRIFIER : absence de rapport");
    expect(marqueur.tagName).toBe("MARK");
  });

  it("transforme une URL source en lien cliquable ouvrant un nouvel onglet", () => {
    render(<RichOutput texte="Source : https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006419285" />);
    const lien = screen.getByRole("link", { name: /consulter la source/i });
    expect(lien.tagName).toBe("A");
    expect(lien).toHaveAttribute("href", "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006419285");
    expect(lien).toHaveAttribute("target", "_blank");
    expect(lien).toHaveAttribute("rel", expect.stringContaining("noopener"));
  });

  it("n'inclut pas la ponctuation de fin de phrase dans l'URL du lien", () => {
    render(<RichOutput texte="Voir https://www.courdecassation.fr/decision/abc123." />);
    const lien = screen.getByRole("link", { name: /consulter la source/i });
    expect(lien).toHaveAttribute("href", "https://www.courdecassation.fr/decision/abc123");
    // Le point final reste affiché, juste hors du lien.
    expect(lien.parentElement?.textContent?.endsWith(".")).toBe(true);
  });
});
