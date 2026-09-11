/**
 * i18n/index.ts — Initialisation i18next (voir "Chantier : internationalisation
 * français / anglais"). Langue mémorisée en localStorage
 * ("plaidia_langue"), appliquée immédiatement (i18next notifie tous les
 * composants qui appellent useTranslation() dès i18n.changeLanguage(),
 * sans rechargement de page) -- français par défaut si rien n'est stocké
 * ou si la valeur stockée n'est pas reconnue.
 *
 * La langue choisie est aussi celle envoyée au backend à chaque appel API
 * (en-tête X-Langue, voir frontend/src/api/http.ts) -- c'est
 * i18n.language, lu directement depuis cette même instance, qui fait foi
 * des deux côtés (affichage ET génération), jamais deux réglages distincts
 * qui pourraient diverger.
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import fr from "./locales/fr.json";
import en from "./locales/en.json";

export const CLE_LANGUE_STOCKEE = "plaidia_langue";
export const LANGUES_SUPPORTEES = ["fr", "en"] as const;
export type Langue = (typeof LANGUES_SUPPORTEES)[number];

/** Exportée uniquement pour les tests (voir SelecteurLangue.test.tsx) --
 * l'appel réel n'a lieu qu'une fois, ici même, au chargement du module. */
export function langueInitiale(): Langue {
  try {
    const stockee = window.localStorage.getItem(CLE_LANGUE_STOCKEE);
    if (stockee && (LANGUES_SUPPORTEES as readonly string[]).includes(stockee)) return stockee as Langue;
  } catch {
    // localStorage indisponible (navigation privée, contexte restreint...) -- français par défaut, sans erreur.
  }
  return "fr";
}

void i18n
  .use(initReactI18next)
  .init({
    resources: { fr: { translation: fr }, en: { translation: en } },
    lng: langueInitiale(),
    fallbackLng: "fr",
    interpolation: { escapeValue: false }, // React échappe déjà -- pas besoin d'un second échappement par i18next.
    returnNull: false,
  });

/** Change la langue active et la persiste -- à utiliser partout plutôt que
 * i18n.changeLanguage() directement, pour ne jamais oublier la persistance
 * (voir SelecteurLangue.tsx). */
export function definirLangue(langue: Langue): void {
  void i18n.changeLanguage(langue);
  try {
    window.localStorage.setItem(CLE_LANGUE_STOCKEE, langue);
  } catch {
    // Le changement reste appliqué pour la session en cours même si la persistance échoue.
  }
}

export default i18n;
