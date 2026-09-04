/**
 * corpus.ts — Constantes du corpus juridique multi-source (Le Grimoire :
 * Importer un texte / Gérer le corpus multi-source). Les sources listées
 * ici sont des suggestions pour le formulaire d'import ; le backend accepte
 * n'importe quelle chaîne (db.py::ajouter_texte_corpus ne valide pas contre
 * une liste fermée), d'où le choix "Autre" ouvrant un champ libre.
 */

export const SOURCES_CORPUS = ["OHADA", "Union européenne", "Sénégal", "CEDEAO", "CEDH", "Autre"];

export const TYPES_TEXTE_CORPUS = ["Loi", "Règlement", "Traité", "Directive", "Convention", "Jurisprudence", "Autre"];
