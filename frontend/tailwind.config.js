/**
 * tailwind.config.js — Design system de Plaid'IA.
 *
 * Les couleurs sont exposées via des variables CSS (définies dans
 * src/styles/globals.css) au format "R G B" pour que les modificateurs
 * d'opacité Tailwind fonctionnent nativement : bg-gold-500/20,
 * border-amethyst-400/40, etc.
 *
 * Voir DESIGN.md pour la justification de chaque token — ce fichier ne
 * doit jamais diverger de ce document.
 */

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: false, // thème sombre unique et permanent — pas de bascule clair/sombre
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "rgb(var(--color-void) / <alpha-value>)",
        surface: {
          DEFAULT: "rgb(var(--color-surface) / <alpha-value>)",
          2: "rgb(var(--color-surface-2) / <alpha-value>)",
          3: "rgb(var(--color-surface-3) / <alpha-value>)",
        },
        gold: {
          300: "rgb(var(--color-gold-300) / <alpha-value>)",
          400: "rgb(var(--color-gold-400) / <alpha-value>)",
          500: "rgb(var(--color-gold-500) / <alpha-value>)",
          600: "rgb(var(--color-gold-600) / <alpha-value>)",
          700: "rgb(var(--color-gold-700) / <alpha-value>)",
          DEFAULT: "rgb(var(--color-gold-500) / <alpha-value>)",
        },
        amethyst: {
          300: "rgb(var(--color-amethyst-300) / <alpha-value>)",
          400: "rgb(var(--color-amethyst-400) / <alpha-value>)",
          600: "rgb(var(--color-amethyst-600) / <alpha-value>)",
          700: "rgb(var(--color-amethyst-700) / <alpha-value>)",
          DEFAULT: "rgb(var(--color-amethyst-400) / <alpha-value>)",
        },
        ivory: "rgb(var(--color-ivory) / <alpha-value>)",
        warmgray: "rgb(var(--color-warmgray) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        risk: {
          high: "rgb(var(--color-risk-high) / <alpha-value>)",
          medium: "rgb(var(--color-risk-medium) / <alpha-value>)",
          low: "rgb(var(--color-risk-low) / <alpha-value>)",
        },
        verify: {
          bg: "rgb(var(--color-verify-bg) / <alpha-value>)",
          text: "rgb(var(--color-verify-text) / <alpha-value>)",
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', "serif"],
        serif: ['"Cormorant Garamond"', "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        display: ["3rem", { lineHeight: "1.1", letterSpacing: "-0.01em" }],
        h1: ["2.25rem", { lineHeight: "1.15" }],
        h2: ["1.75rem", { lineHeight: "1.2" }],
        h3: ["1.375rem", { lineHeight: "1.3" }],
        h4: ["1.125rem", { lineHeight: "1.35" }],
        body: ["1rem", { lineHeight: "1.6" }],
        small: ["0.875rem", { lineHeight: "1.5" }],
        micro: ["0.75rem", { lineHeight: "1.4", letterSpacing: "0.06em" }],
      },
      borderRadius: {
        sm: "4px",
        md: "6px", // défaut : cartes, boutons, inputs — "peu arrondi", pas de rounded-lg par défaut
        lg: "10px",
        pill: "999px",
      },
      boxShadow: {
        card: "0 2px 12px -2px rgb(var(--color-void) / 0.55)",
        "card-hover":
          "0 10px 32px -8px rgb(var(--color-amethyst-600) / 0.4), 0 2px 12px -2px rgb(var(--color-void) / 0.6)",
        "glow-gold": "0 0 24px -6px rgb(var(--color-gold-400) / 0.55)",
        "ring-amethyst": "0 0 0 3px rgb(var(--color-amethyst-400) / 0.35)",
      },
      maxWidth: {
        prose: "65ch",
      },
      backgroundImage: {
        "gothic-arch": "var(--motif-gothic-arch)", // motif secondaire, usage imprimé (DESIGN.md §4)
        grain: "var(--motif-grain)",
      },
    },
  },
  plugins: [],
};
