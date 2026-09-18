import { describe, expect, it } from "vitest";
import type { DocumentGenere } from "@/api";
import { synthetiser } from "../synthese";

// Mercredi 16 septembre 2026, midi.
const MAINTENANT = new Date(2026, 8, 16, 12, 0, 0);

let compteur = 0;
function doc(feature: string, contenu: Record<string, unknown>, dateModification: string): DocumentGenere {
  compteur += 1;
  return {
    id: compteur,
    dossier_id: 1,
    feature,
    titre: `${feature} ${compteur}`,
    parametres: {},
    contenu,
    statut: "Brouillon",
    date_creation: dateModification,
    date_modification: dateModification,
  };
}

function delai(dateEcheance: string, libelle = "Appel") {
  return { type: "appel_civil", libelle, reference: "art. 538 CPC", duree: "1 mois", point_de_depart: "Signification", date_depart: "2026-01-01", echeance_brute: dateEcheance, date_echeance: dateEcheance, proroge: false, precision: "" };
}

describe("synthetiser", () => {
  it("dossier sans document : tout est vide", () => {
    expect(synthetiser([], MAINTENANT)).toEqual({
      prochaineEcheance: null,
      echeancesDepassees: 0,
      nombrePieces: null,
      dernierEntrainement: null,
      recents: [],
    });
  });

  it("prochaine échéance : la plus proche non dépassée, les passées sont comptées à part", () => {
    const synthese = synthetiser(
      [doc("delais", { delais: [delai("2026-09-10", "Passée"), delai("2026-10-30", "Lointaine"), delai("2026-09-20", "Proche")] }, "2026-09-15T10:00:00")],
      MAINTENANT
    );
    expect(synthese.prochaineEcheance?.delai.libelle).toBe("Proche");
    expect(synthese.prochaineEcheance?.jours).toBe(4);
    expect(synthese.echeancesDepassees).toBe(1);
  });

  it("une échéance à la date du jour est à 0 jour, pas dépassée", () => {
    const synthese = synthetiser([doc("delais", { delais: [delai("2026-09-16")] }, "2026-09-15T10:00:00")], MAINTENANT);
    expect(synthese.prochaineEcheance?.jours).toBe(0);
    expect(synthese.echeancesDepassees).toBe(0);
  });

  it("seul le calcul de délais le plus récent fait foi", () => {
    const synthese = synthetiser(
      [
        doc("delais", { delais: [delai("2026-09-01", "Ancien calcul")] }, "2026-09-01T10:00:00"),
        doc("delais", { delais: [delai("2026-12-01", "Nouveau calcul")] }, "2026-09-10T10:00:00"),
      ],
      MAINTENANT
    );
    expect(synthese.prochaineEcheance?.delai.libelle).toBe("Nouveau calcul");
    expect(synthese.echeancesDepassees).toBe(0);
  });

  it("que des échéances dépassées : pas de prochaine échéance", () => {
    const synthese = synthetiser([doc("delais", { delais: [delai("2026-08-01"), delai("2026-09-01")] }, "2026-09-15T10:00:00")], MAINTENANT);
    expect(synthese.prochaineEcheance).toBeNull();
    expect(synthese.echeancesDepassees).toBe(2);
  });

  it("nombre de pièces : null sans bordereau, 0 pour un bordereau vide", () => {
    expect(synthetiser([], MAINTENANT).nombrePieces).toBeNull();
    expect(synthetiser([doc("bordereau", { pieces: [] }, "2026-09-15T10:00:00")], MAINTENANT).nombrePieces).toBe(0);
    expect(synthetiser([doc("bordereau", { pieces: [{}, {}, {}] }, "2026-09-15T10:00:00")], MAINTENANT).nombrePieces).toBe(3);
  });

  it("dernier entraînement : le plus récent", () => {
    const bilan = (total: number) => ({ sections: [], total_alloue_secondes: 600, total_reel_secondes: 600 + total, total_ecart_secondes: total });
    const synthese = synthetiser(
      [doc("entrainement", bilan(10), "2026-09-01T10:00:00"), doc("entrainement", bilan(99), "2026-09-14T10:00:00")],
      MAINTENANT
    );
    expect(synthese.dernierEntrainement?.total_ecart_secondes).toBe(99);
  });

  it("récents : 5 plus récents, sans les features qui ont leur carte", () => {
    const documents = [
      doc("plan", {}, "2026-09-01T10:00:00"),
      doc("resume", {}, "2026-09-02T10:00:00"),
      doc("chronologie", {}, "2026-09-03T10:00:00"),
      doc("simulateur", {}, "2026-09-04T10:00:00"),
      doc("note_client", {}, "2026-09-05T10:00:00"),
      doc("verification_procedurale", {}, "2026-09-06T10:00:00"),
      doc("delais", { delais: [] }, "2026-09-07T10:00:00"),
      doc("bordereau", { pieces: [] }, "2026-09-08T10:00:00"),
      doc("entrainement", { sections: [] }, "2026-09-09T10:00:00"),
    ];
    const recents = synthetiser(documents, MAINTENANT).recents;
    expect(recents.map((d) => d.feature)).toEqual(["verification_procedurale", "note_client", "simulateur", "chronologie", "resume"]);
  });

  it("contenu inattendu : ne plante pas", () => {
    const synthese = synthetiser(
      [doc("delais", {}, "2026-09-15T10:00:00"), doc("bordereau", { pieces: "x" }, "2026-09-15T10:00:00"), doc("entrainement", {}, "2026-09-15T10:00:00")],
      MAINTENANT
    );
    expect(synthese.prochaineEcheance).toBeNull();
    expect(synthese.nombrePieces).toBeNull();
    expect(synthese.dernierEntrainement).toBeNull();
  });
});
