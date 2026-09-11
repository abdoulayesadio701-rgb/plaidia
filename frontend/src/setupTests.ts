/**
 * setupTests.ts — Chargé avant chaque fichier de test (voir vitest.config.ts,
 * `test.setupFiles`). Ajoute les matchers jest-dom (toBeInTheDocument,
 * toHaveClass...) à `expect`.
 */

import "@testing-library/jest-dom/vitest";
// i18next doit être initialisé avant tout composant qui appelle
// useTranslation() -- normalement fait par main.tsx (jamais chargé en
// test), donc ici pour que toute la suite en bénéficie sans que chaque
// fichier de test ait à y penser.
import "./i18n";
