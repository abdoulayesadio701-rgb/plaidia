# Plaid'IA — Front web (React + Vite + TypeScript + Tailwind)

Interface web de Plaid'IA, consommant l'API FastAPI de `backend/`. Reprend
la logique de `gui.py` (tkinter) — espaces Avocat/Greffier, barre de
commande en langage naturel, balisage des références juridiques
(`[ART:...]`/`[JURISPRUDENCE:...]`/`[VERIF:...]`) — dans une interface
web moderne, sur le design system documenté dans [`DESIGN.md`](./DESIGN.md).

## Installation

```bash
cd frontend
npm install
copy .env.example .env    # Windows ; cp sous macOS/Linux
```

Par défaut, `.env` pointe vers `http://localhost:8000` — lancez d'abord le
backend (voir `backend/README.md`) avant de démarrer le front.

## Lancement

```bash
npm run dev
```

Ouvre `http://localhost:5173`. Le front attend l'API sur `VITE_API_URL`
(CORS déjà configuré côté backend pour ce port par défaut).

## État de ce scaffold

Cette première passe pose l'**infrastructure** : point d'entrée, routeur,
state global, client API typé, layout complet (bandeau, barre de commande,
sidebar, barre de statut), composants communs. **Les pages d'action
(Analyser, Résumer, Plan...) sont encore des `<PagePlaceholder>`** — à
remplacer une à une, route par route, sans toucher au reste :

1. Ouvrez `src/router.tsx`.
2. Repérez l'entrée générée pour la route à implémenter (le chemin vient
   de `src/config/navigation.ts`, source unique pour la Sidebar et le
   routeur).
3. Remplacez son `element: <PagePlaceholder ... />` par la vraie page,
   typiquement dans `src/pages/<espace>/<Action>Page.tsx`, en s'appuyant
   sur `src/api/*` pour les appels et `RichOutput`/`RiskBadge` pour
   l'affichage.

`/styleguide` (hors sidebar) reste une référence vivante du design system.

## Structure

```
frontend/
  DESIGN.md                  # Design system — source de vérité (couleurs, typo, composants)
  tailwind.config.js         # Tokens exposés comme classes Tailwind
  src/
    main.tsx                 # Point d'entrée (ReactDOM.createRoot)
    App.tsx                  # <RouterProvider>
    router.tsx                # Toutes les routes — génère les pages d'action depuis navigation.ts
    vite-env.d.ts             # Types pour import.meta.env
    styles/globals.css        # Variables CSS + classes composants (@layer components)
    config/
      navigation.ts            # Source unique : Sidebar + routeur (espaces, sections, items, requiresDossier)
    store/
      useAppStore.ts            # Dossier actif, espace actif, juridiction, chat, toasts, sidebar
      useActivityStore.ts        # Compteur de requêtes en vol (StatusBar) — séparé pour éviter un cycle d'imports
    hooks/
      useAsync.ts                # Triptyque chargement/erreur/données standard pour les futures pages
    api/
      http.ts                   # fetch typé, gestion d'erreur uniforme, upload, export de fichiers
      types.ts                  # Types miroirs des schémas Pydantic du backend
      dossiers.ts, analyse.ts, jurisprudence.ts, notes.ts, greffier.ts, chat.ts, intention.ts
      index.ts                  # `import { dossiers, analyse, ... } from "@/api"`
    layout/
      AppLayout.tsx              # Squelette général (bandeau + commande + sidebar + statut)
      TopBar.tsx, CommandBar.tsx, Sidebar.tsx, StatusBar.tsx, DossierSelector.tsx
    components/
      RichOutput.tsx              # Rendu dédié [ART:...]/[JURISPRUDENCE:...]/[VERIF:...], interprète **gras**
      RiskBadge.tsx                # Pastille Faible / Moyen / Élevé
      Button.tsx, Modal.tsx, NouveauDossierModal.tsx, Tooltip.tsx
      Spinner.tsx, ErrorState.tsx, ToastContainer.tsx, PagePlaceholder.tsx
      Logo.tsx, GothicMotif.tsx    # Identité visuelle (voir DESIGN.md §4-5)
    pages/
      HomePage.tsx, NotFoundPage.tsx, Styleguide.tsx
```

## Conventions

- **Alias `@/`** → `src/` (configuré dans `vite.config.ts` et `tsconfig.json`).
- **Nommage en français** pour tout ce qui touche au domaine métier
  (`dossierActif`, `chargerDossiers`, `analyserConclusions`...), à
  l'identique de `gui.py`/`analyse.py` — cohérence avec le reste du projet.
- **Chaque fonction de `src/api/*.ts`** correspond une-pour-une à une route
  du backend (voir `backend/README.md`) — en cas de doute sur un type ou
  un endpoint, `/docs` (Swagger) du backend fait foi.
- **Les balises `[ART:...]`/`[JURISPRUDENCE:...]`/`[VERIF:...]`** ne
  doivent jamais être filtrées, reformulées ou redécorées ailleurs que
  dans `RichOutput`/`.marker-verify`/`.marker-citation` — c'est le
  garde-fou anti-hallucination, voir DESIGN.md §1.6.

## Non vérifié

Ce scaffold a été écrit sans exécution locale — **Node.js/npm n'est pas
installé dans l'environnement où il a été généré**, donc ni `npm install`
ni `npm run dev`/`build` n'ont pu être lancés pour le valider. Le code a
été relu attentivement (imports, types, cohérence avec `tailwind.config.js`
et `globals.css`), mais un premier `npm install && npm run dev` chez vous
est la vraie vérification qui manque encore — signalez toute erreur de
compilation rencontrée.
