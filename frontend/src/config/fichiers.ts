/**
 * fichiers.ts — Constantes et utilitaires partagés pour l'import de
 * fichiers dans toute l'application (voir FileDropZone, useImportFichiers).
 * Centralise ce qui était dupliqué à l'identique dans 6 pages avant ce
 * chantier (AUDIT_IMPORT_EXPORT.md) — un seul endroit à modifier si les
 * formats acceptés évoluent.
 */

/** Formats acceptés par l'extraction de texte générique côté backend (voir
 * extract.py::extract_text) — PDF, Word, Excel, texte, images. Toute page
 * qui accepte un "document quelconque" doit utiliser cette liste plutôt
 * que la retaper. */
export const EXTENSIONS_DOCUMENT = [".pdf", ".docx", ".xlsx", ".xls", ".txt", ".png", ".jpg", ".jpeg", ".webp"];

export function formaterTailleFichier(octets: number): string {
  if (octets < 1024) return `${octets} o`;
  if (octets < 1024 * 1024) return `${(octets / 1024).toFixed(0)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}
