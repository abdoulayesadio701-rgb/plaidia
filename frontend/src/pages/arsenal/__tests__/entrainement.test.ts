import { describe, expect, it } from "vitest";
import type { DocumentGenere } from "@/api";
import { demarrerChrono, mettreEnPause, reprendre, secondesEcoulees } from "../chronometre";
import { resumerSeances } from "../seancesEntrainement";

describe("chronomètre avec pause", () => {
  it("compte le temps écoulé depuis le départ", () => {
    expect(secondesEcoulees(demarrerChrono(1_000), 6_400)).toBe(5);
  });

  it("figé pendant la pause", () => {
    const enPause = mettreEnPause(demarrerChrono(0), 10_000);
    expect(secondesEcoulees(enPause, 10_000)).toBe(10);
    expect(secondesEcoulees(enPause, 500_000)).toBe(10);
  });

  it("la reprise ne compte pas le temps de pause", () => {
    // 10 s de parole, 60 s de pause, puis 5 s de parole = 15 s
    const enPause = mettreEnPause(demarrerChrono(0), 10_000);
    const repris = reprendre(enPause, 70_000);
    expect(secondesEcoulees(repris, 70_000)).toBe(10);
    expect(secondesEcoulees(repris, 75_000)).toBe(15);
  });

  it("plusieurs pauses s'enchaînent", () => {
    let etat = demarrerChrono(0);
    etat = reprendre(mettreEnPause(etat, 4_000), 14_000); // 4 s parlées, 10 s de pause
    etat = reprendre(mettreEnPause(etat, 20_000), 50_000); // 6 s parlées de plus, 30 s de pause
    expect(secondesEcoulees(etat, 53_000)).toBe(13);
  });

  it("mettre en pause deux fois, ou reprendre sans pause, ne change rien", () => {
    const enPause = mettreEnPause(demarrerChrono(0), 3_000);
    expect(mettreEnPause(enPause, 9_000)).toBe(enPause);
    const actif = demarrerChrono(0);
    expect(reprendre(actif, 9_000)).toBe(actif);
  });

  it("jamais négatif", () => {
    expect(secondesEcoulees(demarrerChrono(5_000), 1_000)).toBe(0);
  });
});

let compteur = 0;
function seance(ecart: number, date: string, alloue = 600): DocumentGenere {
  compteur += 1;
  return {
    id: compteur, dossier_id: 1, feature: "entrainement", titre: "Entraînement", parametres: {},
    contenu: { sections: [], total_alloue_secondes: alloue, total_reel_secondes: alloue + ecart, total_ecart_secondes: ecart },
    statut: "Brouillon", date_creation: date, date_modification: date,
  };
}

describe("resumerSeances", () => {
  it("aucune séance", () => {
    expect(resumerSeances([])).toEqual([]);
  });

  it("triées de la plus récente à la plus ancienne, première séance sans comparaison", () => {
    const resume = resumerSeances([seance(120, "2026-09-01T10:00:00"), seance(-30, "2026-09-05T10:00:00")]);
    expect(resume.map((s) => s.ecartSecondes)).toEqual([-30, 120]);
    expect(resume[1].progresSecondes).toBeNull();
  });

  it("progrès = réduction de l'écart absolu par rapport à la séance précédente", () => {
    const resume = resumerSeances([
      seance(120, "2026-09-01T10:00:00"),
      seance(-30, "2026-09-05T10:00:00"), // |30| < |120| : +90 s de progrès
      seance(200, "2026-09-09T10:00:00"), // |200| > |30| : -170 s
    ]);
    expect(resume.map((s) => s.progresSecondes)).toEqual([-170, 90, null]);
  });

  it("ignore les documents au contenu inattendu", () => {
    const invalide = { ...seance(0, "2026-09-02T10:00:00"), contenu: {} };
    expect(resumerSeances([invalide, seance(10, "2026-09-03T10:00:00")])).toHaveLength(1);
  });
});
