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
  /** Clé i18next (voir navKey ci-dessous) -- `title` sert de defaultValue. */
  titleKey: string;
  items: NavItem[];
}

/** Dérive la clé i18next d'un NavItem depuis son path ("/arsenal/analyser"
 * -> "nav.arsenal.analyser") -- une seule source de vérité (ce fichier)
 * pour les libellés de navigation, consommée par Sidebar.tsx (et
 * RecentsPanel.tsx via un ElementRecent.path déjà stocké) plutôt que de
 * dupliquer les mêmes clés à la main dans chaque composant. */
export function navKey(path: string): string {
  return `nav${path.replace(/\//g, ".")}`;
}

export const ESPACE_LABELS: Record<Espace, string> = {
  avocat: "⚖️ Avocat",
  greffier: "🖋️ Greffier",
};

export const NAVIGATION: Record<Espace, NavSection[]> = {
  avocat: [
    {
      title: "Poser une question",
      titleKey: "nav.sections.poserQuestion",
      items: [
        { path: "/chat", label: "Échanger avec l'agent juridique", requiresDossier: false },
        { path: "/conversations", label: "Historique des conversations", requiresDossier: false },
      ],
    },
    {
      title: "L'Arsenal",
      titleKey: "nav.sections.arsenal",
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
      titleKey: "nav.sections.chemise",
      items: [
        { path: "/chemise/historique", label: "Historique de ce dossier", requiresDossier: true },
        { path: "/chemise/dossiers", label: "Parcourir mes dossiers", requiresDossier: false },
        { path: "/chemise/preparer", label: "Préparer ce dossier", requiresDossier: true },
      ],
    },
    {
      title: "Le Grimoire",
      titleKey: "nav.sections.grimoire",
      items: [
        { path: "/grimoire/jurisprudence", label: "Consulter la jurisprudence", requiresDossier: false },
        { path: "/grimoire/collecter", label: "Collecter de la jurisprudence", requiresDossier: false },
        { path: "/grimoire/gerer", label: "Gérer la jurisprudence", requiresDossier: false },
        { path: "/grimoire/corpus", label: "Gérer le corpus multi-source", requiresDossier: false },
      ],
    },
    {
      title: "Le Carnet",
      titleKey: "nav.sections.carnet",
      items: [
        { path: "/carnet/note", label: "Prendre une note", requiresDossier: true },
        { path: "/carnet/notes", label: "Consulter les notes", requiresDossier: true },
        { path: "/carnet/note-client", label: "Rédiger une note client", requiresDossier: true },
        { path: "/carnet/traduire", label: "Traduire un texte (FR ↔ EN)", requiresDossier: false },
      ],
    },
  ],
  greffier: [
    {
      title: "Affaire en cours",
      titleKey: "nav.sections.affaireEnCours",
      items: [
        { path: "/greffier/chronologie", label: "Chronologie automatique de cette affaire", requiresDossier: true },
        { path: "/greffier/verification-procedurale", label: "Vérification procédurale", requiresDossier: true },
        { path: "/greffier/delais", label: "Suivi des délais de procédure", requiresDossier: true },
      ],
    },
    {
      title: "Documents",
      titleKey: "nav.sections.documents",
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
      titleKey: "nav.sections.rechercheRedaction",
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
