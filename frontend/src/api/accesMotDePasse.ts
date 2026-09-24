/**
 * accesMotDePasse.ts : stockage du mot de passe d'accès au serveur (voir
 * backend/app/acces.py). Conservé dans localStorage pour ne pas le
 * ressaisir à chaque onglet : il reste donc sur ce navigateur jusqu'à
 * "Se déconnecter" ou jusqu'à ce que le serveur le refuse. Envoyé
 * uniquement en en-tête X-Acces-Mot-De-Passe vers l'API.
 */

const CLE_STORAGE = "plaidia_acces_mot_de_passe";

export const EN_TETE_ACCES = "X-Acces-Mot-De-Passe";

export function obtenirMotDePasseAcces(): string | null {
  try {
    return localStorage.getItem(CLE_STORAGE);
  } catch {
    return null;
  }
}

export function definirMotDePasseAcces(valeur: string | null): void {
  try {
    if (valeur && valeur.trim()) localStorage.setItem(CLE_STORAGE, valeur.trim());
    else localStorage.removeItem(CLE_STORAGE);
  } catch {
    // Stockage indisponible : le mot de passe sera redemandé à chaque visite.
  }
}
