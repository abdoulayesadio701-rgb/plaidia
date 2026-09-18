/** cheminsDocuments.ts — page qui affiche chaque type de document généré, partagé par
 * l'historique du dossier, sa recherche et le tableau de bord. */

// Chemin de la page Arsenal/Greffier/Carnet qui affiche ce type de document
// généré -- tenu à jour à chaque nouvelle fonctionnalité persistée (voir
// db.creer_document_genere). Défaut (feature inconnue) : grimoire/jurisprudence.
export const CHEMIN_PAR_FEATURE = {
  plan: "arsenal/plan",
  simulateur: "arsenal/simulateur",
  resume: "arsenal/resumer",
  chronologie: "greffier/chronologie",
  verification_procedurale: "greffier/verification-procedurale",
  note_client: "carnet/note-client",
  delais: "greffier/delais",
  entrainement: "arsenal/entrainement",
  bordereau: "chemise/bordereau",
  // Ces deux features ne viennent pas de documents_generes (voir
  // db.rechercher_dans_documents_dossier) : pas d'id de document
  // individuellement adressable, le lien renvoie vers la page générale.
  conclusions: "arsenal/analyser",
  notes: "carnet/notes",
} as const;

export function cheminDocument(feature: string): string {
  return CHEMIN_PAR_FEATURE[feature as keyof typeof CHEMIN_PAR_FEATURE] ?? "grimoire/jurisprudence";
}
