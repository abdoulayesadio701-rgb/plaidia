/**
 * cleApiPersonnelle.ts — Stockage de la clé Anthropic personnelle
 * ("Utiliser ma propre clé Anthropic", voir Footer/StatusBar). Uniquement
 * dans sessionStorage (jamais localStorage, jamais envoyée ailleurs qu'en
 * en-tête X-Anthropic-Api-Key) : elle disparaît à la fermeture de l'onglet,
 * n'est jamais journalisée côté serveur (voir backend/app/main.py) ni
 * relue par aucune autre origine.
 */

const CLE_STORAGE_KEY = "plaidia_cle_anthropic_perso";

export function obtenirClePersonnelle(): string | null {
  try {
    return sessionStorage.getItem(CLE_STORAGE_KEY);
  } catch {
    // sessionStorage indisponible (navigation privée stricte, etc.)
    return null;
  }
}

export function definirClePersonnelle(cle: string | null): void {
  try {
    if (cle && cle.trim()) sessionStorage.setItem(CLE_STORAGE_KEY, cle.trim());
    else sessionStorage.removeItem(CLE_STORAGE_KEY);
  } catch {
    // Silencieux : au pire la clé n'est pas mémorisée pour cet onglet.
  }
}
