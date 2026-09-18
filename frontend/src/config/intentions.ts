/**
 * intentions.ts — page ouverte par chaque action reconnue par le routeur
 * d'intention (root analyse.py::INTENTION_SYSTEM_PROMPT). Les actions
 * "export", "domaine", "menu" et "quitter" en sont absentes : ce sont des
 * gestes ponctuels sur une page déjà ouverte, pas des destinations.
 */

export const ROUTES_PAR_ACTION: Record<string, string> = {
  analyser: "/arsenal/analyser",
  resumer: "/arsenal/resumer",
  plan: "/arsenal/plan",
  simulateur: "/arsenal/simulateur",
  rapport: "/arsenal/rapport-complet",
  note: "/carnet/note",
  notes_consulter: "/carnet/notes",
  note_client: "/carnet/note-client",
  chronologie: "/greffier/chronologie",
  verification: "/greffier/verification-procedurale",
  delais: "/greffier/delais",
  entrainement: "/arsenal/entrainement",
  bordereau: "/chemise/bordereau",
  importer: "/chemise/preparer",
};
