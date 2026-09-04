/**
 * navigation.ts — Source unique de vérité pour la Sidebar et le routeur.
 *
 * Reprend telle quelle la structure de gui.py (self.categories) : deux
 * espaces (Avocat / Greffier), chacun décomposé en catégories, chaque
 * catégorie listant ses actions avec `requiresDossier` — c'est ce booléen
 * qui détermine si l'entrée est désactivée (avec tooltip) tant qu'aucun
 * dossier n'est sélectionné.
 */

export type Espace = "avocat" | "greffier";

export interface NavItem {
  path: string;
  label: string;
  /** Bref descriptif utilisé dans le tooltip quand l'action est désactivée. */
  description?: string;
  requiresDossier: boolean;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const ESPACE_LABELS: Record<Espace, string> = {
  avocat: "⚖️ Avocat",
  greffier: "🖋️ Greffier",
};

export const NAVIGATION: Record<Espace, NavSection[]> = {
  avocat: [
    {
      title: "Poser une question",
      items: [{ path: "/chat", label: "Échanger avec l'agent juridique", requiresDossier: false }],
    },
    {
      title: "L'Arsenal",
      items: [
        { path: "/arsenal/analyser", label: "Analyser des conclusions adverses", requiresDossier: true },
        { path: "/arsenal/resumer", label: "Résumer ce dossier", requiresDossier: true },
        { path: "/arsenal/plan", label: "Générer un plan de plaidoirie", requiresDossier: true },
        { path: "/arsenal/simulateur", label: "Simuler les objections probables", requiresDossier: true },
        { path: "/arsenal/rapport-complet", label: "Rapport complet", requiresDossier: true },
        { path: "/arsenal/style", label: "Analyse stylistique des conclusions adverses", requiresDossier: false },
        { path: "/arsenal/verification-procedurale", label: "Vérification procédurale", requiresDossier: true },
      ],
    },
    {
      title: "La Chemise",
      items: [
        { path: "/chemise/historique", label: "Historique de ce dossier", requiresDossier: true },
        { path: "/chemise/dossiers", label: "Parcourir mes dossiers", requiresDossier: false },
        { path: "/chemise/preparer", label: "Préparer ce dossier", requiresDossier: true },
      ],
    },
    {
      title: "Le Grimoire",
      items: [
        { path: "/grimoire/jurisprudence", label: "Consulter la jurisprudence", requiresDossier: false },
        { path: "/grimoire/collecter", label: "Collecter de la jurisprudence", requiresDossier: false },
        { path: "/grimoire/gerer", label: "Gérer la jurisprudence", requiresDossier: false },
        { path: "/grimoire/corpus", label: "Gérer le corpus multi-source", requiresDossier: false },
      ],
    },
    {
      title: "Le Carnet",
      items: [
        { path: "/carnet/note", label: "Prendre une note", requiresDossier: true },
        { path: "/carnet/notes", label: "Consulter les notes", requiresDossier: true },
        { path: "/carnet/note-client", label: "Rédiger une note client", requiresDossier: true },
      ],
    },
  ],
  greffier: [
    {
      title: "Affaire en cours",
      items: [
        { path: "/greffier/chronologie", label: "Chronologie automatique de cette affaire", requiresDossier: true },
        { path: "/greffier/verification-procedurale", label: "Vérification procédurale", requiresDossier: true },
      ],
    },
    {
      title: "Documents",
      items: [
        { path: "/greffier/extraction", label: "Extraction d'éléments clés d'un document", requiresDossier: false },
        { path: "/greffier/classement", label: "Classement automatique d'un document", requiresDossier: false },
        { path: "/greffier/coherence", label: "Contrôle de cohérence entre documents", requiresDossier: false },
        { path: "/greffier/requisitoire", label: "Analyser un réquisitoire", requiresDossier: false },
        { path: "/greffier/rapport-instruction", label: "Rapport d'instruction", requiresDossier: false },
      ],
    },
    {
      title: "Recherche & rédaction",
      items: [
        { path: "/greffier/recherche", label: "Rechercher dans toutes les affaires", requiresDossier: false },
        { path: "/greffier/pv-audience", label: "Rédiger un procès-verbal d'audience", requiresDossier: false },
      ],
    },
  ],
};

/** Tous les items, toutes catégories/espaces confondus — pratique pour générer les routes. */
export function allNavItems(): NavItem[] {
  return Object.values(NAVIGATION).flatMap((sections) => sections.flatMap((section) => section.items));
}

/** Retrouve la définition de navigation correspondant à un chemin (pour la CommandBar, le titre de page...). */
export function findNavItem(path: string): NavItem | undefined {
  return allNavItems().find((item) => item.path === path);
}
