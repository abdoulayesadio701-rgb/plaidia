# Plaid'IA — Design System

Identité visuelle de référence pour le front web de Plaid'IA : un cabinet
d'avocat ancien, revisité sans pastiche — la balance de justice en or
ancien et la rigueur d'un bureau feutré, jamais l'univers "fantasy". Le
sérieux du fond noir doit rester lisible, professionnel, utilisable des
heures durant par un avocat en train de travailler un dossier.

**Thème clair uniquement** — retheme SaaS violet (dominante violet/mauve,
cartes blanches sur fond gris très clair, texte presque noir, touches
bleu nuit). Tous les tokens ci-dessous n'ont qu'une seule définition. Les
noms de tokens n'ont pas changé (`gold-*` reste la couleur principale,
`amethyst-*` reste l'accent d'état) — seules leurs valeurs ont été
retravaillées ; la prose ci-dessous ("or ancien", "fond noir violacé",
cabinet d'avocat ancien) décrit l'identité précédente et reste à
réécrire, mais les tableaux de valeurs qui suivent sont à jour.

Ce fichier est la source de vérité. `tailwind.config.js` et
`src/styles/globals.css` doivent rester synchronisés avec les valeurs
listées ici — si vous changez une couleur, changez-la aux trois endroits.

---

## 1. Couleur

### 1.1 Fond — noir violacé

| Token | Hex | RGB | Usage |
|---|---|---|---|
| `void` | `#F7F7F9` | 247 247 249 | Fond de page, gris très clair |
| `surface` | `#FFFFFF` | 255 255 255 | Cartes, panneaux, barre latérale |
| `surface-2` | `#F1F1F4` | 241 241 244 | Éléments légèrement distincts : inputs, dropdowns, lignes de tableau survolées |
| `surface-3` | `#E5E5EA` | 229 229 234 | Bordures |

Beaucoup d'espaces blancs, cartes blanches nettes sur fond gris clair —
plus de dégradé violet-noir sous les surfaces.

### 1.2 Violet — couleur principale

| Token | Hex | RGB | Usage |
|---|---|---|---|
| `gold-300` | `#DEC8E8` | 222 200 232 | Fond de badge violet très pâle, surlignage discret |
| `gold-400` | `#A968BE` | 169 104 190 | Violet clair — reflets, hover des boutons primaires, icônes actives |
| `gold-500` | `#8B4BA8` | 139 75 168 | **Couleur principale** — icônes, séparateurs, bouton primaire au repos |
| `gold-600` | `#66377F` | 102 55 127 | Violet foncé — bordures fines |
| `gold-700` | `#522C66` | 82 44 102 | État pressé/actif des boutons violets |

`gold-500` reste LA couleur de marque et d'action primaire, `gold-400`
réservé au hover/reflet, `gold-600` aux bordures fines et aux fonds. Les
titres (h1-h4) utilisent désormais `amethyst-600` (navy), pas `gold-500`
— voir §1.3.

### 1.3 Accent purple + navy — accent et titres

| Token | Hex | RGB | Usage |
|---|---|---|---|
| `amethyst-300` | `#D4A8E0` | 212 168 224 | Fond de badge/pastille très pâle |
| `amethyst-400` | `#9B59B6` | 155 89 182 | **Focus ring**, états actifs, barre de progression, liens |
| `amethyst-600` | `#17233C` | 23 35 60 | Navy — titres (h1-h4), ombres portées, dégradés premium |
| `amethyst-700` | `#111A2D` | 17 26 45 | État pressé des éléments navy |

Règle : le violet (`gold-*`) est la couleur d'action primaire (boutons) ;
`amethyst-400` (accent purple) sert pour l'état — sélection, focus
clavier, onglet actif, progression ; `amethyst-600` (navy) sert pour les
titres et les ombres/dégradés "premium", jamais pour un bouton primaire.

### 1.4 Texte

| Token | Hex | RGB | Usage |
|---|---|---|---|
| `ivory` | `#202124` | 32 33 36 | Texte de corps, presque noir, sur tout fond clair |
| `warmgray` | `#6B7280` | 107 114 128 | Texte secondaire, légendes, métadonnées |
| `muted` | `#9CA3AF` | 156 163 175 | Placeholder, texte désactivé, texte tertiaire |
| `ink` | `#FFFFFF` | 255 255 255 | Texte sur fond violet (boutons primaires) |

### 1.5 Risque (analyse de conclusions adverses)

| Token | Hex | RGB | Niveau |
|---|---|---|---|
| `risk-high` | `#B3261E` | 179 38 30 | Élevé — rouge brique |
| `risk-medium` | `#B8860B` | 184 134 11 | Moyen — ambre |
| `risk-low` | `#4C6B3F` | 76 107 63 | Faible — vert sauge |

Ce sont des couleurs **sémantiques**, indépendantes de l'accent améthyste
— ne jamais les confondre avec les états actif/focus.

### 1.6 Marqueur "À VÉRIFIER" — garde-fou anti-hallucination

| Token | Hex | RGB | Usage |
|---|---|---|---|
| `verify-bg` | `#FFE9B0` | 255 233 176 | Fond ambre pâle |
| `verify-text` | `#7A4A00` | 122 74 0 | Texte brun, toujours en gras |

Un des deux seuls éléments à fond clair de toute l'interface (l'autre est
le parchemin, §1.8) — intentionnel : il doit sauter aux yeux au milieu
d'une page sombre. Ne jamais l'adoucir, ne jamais réduire son contraste,
ne jamais le remplacer par une simple couleur de texte. Ces deux valeurs
sont reprises telles quelles de `gui.py` (tag `a_verifier`) pour la
continuité visuelle entre l'ancienne interface tkinter et le nouveau
front.

### 1.8 Parchemin — dépôt de pièce

La seconde (et dernière) exception délibérée au fond sombre : la zone de
saisie de `TexteLongModal` (coller un réquisitoire, des conclusions...)
est un îlot de parchemin clair, scellé d'un médaillon noir cerclé d'or —
une vraie photographie de la balance (voir `assets/sceau-justice.jpg`),
assombrie et cerclée façon cachet, craquelée d'un trait doré façon
kintsugi à l'ouverture — classes `.wax-seal` / `.seal-photo-*` /
`.parchment-*` dans `globals.css`. Le geste (déposer une pièce longue
dans le dossier) justifie ce traitement chaleureux et concret, à
l'inverse du reste de l'UI qui reste fonctionnelle et sombre. Ne pas
généraliser ce motif à d'autres formulaires sans la même justification
narrative — ce n'est pas un composant "carte claire" réutilisable au sens
large, seulement un habillage pour ce geste précis (et ses futurs
équivalents : coller un long texte à analyser ailleurs dans l'app).

| Token (hex en dur, non repris dans `:root`) | Usage |
|---|---|
| `#f6efdf` → `#ddcda3` | Dégradé du parchemin |
| `#2b2016` | Texte (encre) |
| `#8a7455` | Filigrane / texte d'accroche, italique |
| Médaillon : photo réelle, cerclée `gold-600/60`, assombrie (`brightness(.72) contrast(1.3)`) | Cachet — noir et or, pas de dégradé améthyste |
| Craquelure : `gold-400` | Trait qui se dessine à l'ouverture, façon kintsugi (l'or répare/révèle, ne cache pas) |

### 1.9 Bordures

Bordure fine dorée à faible opacité pour délimiter les cartes et
panneaux : `border-gold-600/20` (20 % d'opacité) au repos,
`border-gold-500/40` au survol. Jamais de bordure grise neutre.

---

## 2. Typographie

| Rôle | Police | Fallback | Usage |
|---|---|---|---|
| **Display** | Playfair Display | serif | Réservée au mot-marque "Plaid'IA" et au titre principal d'une page d'accueil. Jamais pour un titre de section courant — trop dramatique en usage répété. |
| **Serif** | Cormorant Garamond | serif | `h1`–`h4` de contenu, intitulés de carte, citations. La voix "cabinet ancien" du produit. |
| **Sans** | Inter | system-ui, sans-serif | Tout le texte de corps, boutons, formulaires, UI dense. |
| **Mono** | JetBrains Mono | ui-monospace, monospace | Références juridiques (articles de loi, numéros RG, réf. Judilibre/Légifrance, "À VÉRIFIER" inline dans du texte technique). |

Import (Google Fonts, à placer dans `index.html` ou en tête de
`globals.css`) :

```
https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap
```

### Échelle

| Token | Taille | Interligne | Police | Usage |
|---|---|---|---|---|
| `display` | 3rem / 48px | 1.1 | Playfair Display 700 | Mot-marque, hero |
| `h1` | 2.25rem / 36px | 1.15 | Cormorant Garamond 600 | Titre de page |
| `h2` | 1.75rem / 28px | 1.2 | Cormorant Garamond 600 | Titre de section |
| `h3` | 1.375rem / 22px | 1.3 | Cormorant Garamond 600 | Titre de carte |
| `h4` | 1.125rem / 18px | 1.35 | Cormorant Garamond 500 | Sous-titre, label de groupe |
| `body` | 1rem / 16px | 1.6 | Inter 400 | Corps de texte |
| `small` | 0.875rem / 14px | 1.5 | Inter 400 | Légendes, métadonnées |
| `micro` | 0.75rem / 12px | 1.4 | Inter 500, tracking large | Labels de badge, éléments UI minuscules |
| `mono` | 0.875rem / 14px | 1.5 | JetBrains Mono 400 | Références juridiques |

Titres en `text-wrap: balance`. Largeur de ligne du corps de texte
plafonnée à ~65 caractères (`max-w-prose` / `65ch`) dans les zones de
lecture longue (réponses du chat, notes structurées).

---

## 3. Forme

### Rayon de bordure — "peu arrondi", jamais `rounded-full` sauf pastilles

| Token | Valeur | Usage |
|---|---|---|
| `radius-sm` | 4px | Petits éléments : tag, checkbox |
| `radius-md` | 6px | **Défaut** — cartes, boutons, inputs |
| `radius-lg` | 10px | Modales, popovers |
| `radius-pill` | 999px | Badges de risque, pastilles d'état uniquement |

### Ombres — douces, violettes, jamais noires pures

| Token | Valeur | Usage |
|---|---|---|
| `shadow-card` | `0 2px 12px -2px rgb(11 10 15 / 0.55)` | Carte au repos |
| `shadow-card-hover` | `0 10px 32px -8px rgb(110 63 163 / 0.4), 0 2px 12px -2px rgb(11 10 15 / 0.6)` | Carte au survol — le violet devient visible |
| `shadow-glow-gold` | `0 0 24px -6px rgb(230 199 106 / 0.55)` | Halo au survol d'un bouton primaire |
| `shadow-ring-amethyst` | `0 0 0 3px rgb(139 92 246 / 0.35)` | Anneau de focus clavier, sur tout élément interactif |

---

## 4. Composants

### Boutons

- **Primaire** : fond `gold-500`, texte `ink` (quasi-noir, jamais blanc),
  `radius-md`, poids `font-semibold`. Survol : fond `gold-400` +
  `shadow-glow-gold`. Actif/pressé : fond `gold-700`. Désactivé : fond
  `gold-500/30`, texte `muted`, pas de survol.
- **Secondaire** : fond transparent, bordure 1px `gold-600/50`, texte
  `gold-500`. Survol : fond `gold-500/10`, bordure `gold-500`. Jamais de
  fond plein sur le secondaire — c'est ce qui le distingue du primaire.
- **Fantôme (tertiaire)** : pas de bordure, texte `amethyst-400`, souligné
  au survol. Réservé aux actions basses priorité (liens inline, "annuler").
- Tous les boutons : focus clavier = `shadow-ring-amethyst`, jamais de
  `outline` navigateur par défaut.

### Cartes

Fond `surface`, bordure 1px `gold-600/20`, `radius-md` (6px),
`shadow-card` au repos. Au survol (si cliquable) : bordure `gold-500/40`,
`shadow-card-hover`, légère translation `-2px` en Y. Padding interne
généreux (`p-6` desktop / `p-4` mobile) — le contenu ne touche jamais le
bord.

### Inputs

Fond `surface-2`, bordure 1px `surface-3` (quasi invisible au repos),
texte `ivory`, placeholder `muted`, `radius-md`. **Au focus** : bordure
`amethyst-400` + `shadow-ring-amethyst`. Jamais de bordure dorée sur un
input — l'or est réservé à la marque et à l'action, l'améthyste à l'état.

### Badges de risque

Pilule (`radius-pill`), fond de la couleur de risque à 15 % d'opacité,
texte plein de la même couleur, bordure 1px de la même couleur à 30 %.
Toujours accompagnés du mot ("Élevé", "Moyen", "Faible"), jamais de la
couleur seule — accessibilité daltonisme.

### Marqueur "À VÉRIFIER"

`<mark>` sémantique, fond `verify-bg`, texte `verify-text` en
`font-bold`, `radius-sm`, padding horizontal léger (`px-1`). Inline dans
le flux de texte, jamais en bloc à part — il doit interrompre visuellement
la lecture exactement là où la vérification est nécessaire.

### Onglets (tabs)

Ligne de fond `surface`, séparateur bas `gold-600/20`. Onglet actif :
texte `amethyst-400`, indicateur bas `amethyst-400` 2px. Onglets inactifs :
texte `warmgray`, survol texte `ivory`.

### Atmosphère du bloc d'accueil — grain + lueurs, plutôt que l'arche seule

Retour d'usage : une arche gothique en filigrane, seule, lisait comme un
fond d'écran plus que comme une identité de marque — trop illustrative,
pas assez "produit". Le traitement retenu pour le hero superpose :

1. **Grain** — texture de bruit (SVG `feTurbulence`, `mix-blend-mode:
   overlay`, opacité ~5 %) sur toute la page, pour éviter l'aplat noir
   trop lisse qui lit comme une maquette non finie.
2. **Lueurs ambiantes** — deux masses radiales floutées (`blur(90px)`),
   une or (`gold-600` à 16 %) et une améthyste (`amethyst-600` à 20 %),
   positionnées en diagonale derrière le texte du hero.
3. **Une fenêtre produit** — pas un fond décoratif abstrait : une vraie
   carte de résultat (badge de risque, syllogisme, marqueur "À
   VÉRIFIER") légèrement inclinée en perspective, qui EST la thèse
   visuelle du produit. Voir "Show the page at rest" — le hero doit
   montrer ce que l'outil fait, pas seulement évoquer une ambiance.

L'arche gothique (`src/components/GothicMotif.tsx`, conservée) reste
disponible comme motif **secondaire** — utilisable en filigrane très
discret sur un support imprimé (page de garde d'export PDF/Word) où
l'ambiance "cabinet ancien" prime sur la démonstration produit — mais
n'est plus le traitement par défaut du hero web.

---

## 5. Logo / mot-marque

Glyphe balance **abstrait**, 7 primitives : un fléau à peine arqué (pas
une ligne rigide), deux fils descendant vers des plateaux réduits à un
point, un fût, une base. `gold-500`, épaisseur de trait constante (pas
de dégradé sur les tracés — le dégradé est réservé aux surfaces).

Historique de la décision : une première itération reprenait
littéralement l'ornementation du mood-board de référence (fronton à
quatrefeuille, bras à volutes, socle à degrés, chaîne perlée) — jugée
trop illustrative, plus proche du blason gravé que d'une marque
d'aujourd'hui. L'abstraction actuelle porte mieux à toute échelle
(barre latérale, favicon ~16-24px) sans perdre le sujet — voir
`src/components/Logo.tsx` pour le tracé complet et le commentaire de
décision.

**Exception unique à la règle "icône tout en or"** : un cabochon
`amethyst-400` plein au point de pivot du fléau, seule touche de couleur
sur une icône sinon monochrome — signature directe reprise du pommeau
serti d'améthyste de la dague de référence. Seul détail conservé de la
première itération. Ce cabochon ne doit jamais se multiplier ailleurs
sur l'icône ; c'est un unique point focal, pas une décoration répétée.

Mot-marque "Plaid'IA" en Playfair Display 700, `gold-500`, avec
l'apostrophe traitée comme une vraie apostrophe typographique (’) et non
une apostrophe droite ('). Toujours l'icône à gauche du mot-marque,
jamais l'inverse, espacement `gap-2.5`.

---

## 6. Accessibilité

- Contraste `ivory` sur `void`/`surface` : ≥ 12:1 (largement au-dessus du
  AA 4.5:1).
- Contraste `warmgray` sur `surface` : ≥ 4.6:1 — reste conforme AA pour
  du texte normal.
- Contraste `ink` sur `gold-500` : ≥ 8:1.
- `verify-text` sur `verify-bg` : ≥ 7:1 (AAA) — c'est le point du
  marqueur, il doit rester lisible même en cas de daltonisme partiel.
- Le focus clavier (`shadow-ring-amethyst`) est appliqué systématiquement
  via `:focus-visible`, jamais supprimé.
- Les badges de risque portent toujours le libellé textuel, jamais la
  seule couleur.

---

## 7. Fichiers

| Fichier | Rôle |
|---|---|
| `DESIGN.md` | Ce document — la source de vérité |
| `tailwind.config.js` | Tokens couleur/police/rayon/ombre exposés comme classes utilitaires Tailwind |
| `src/styles/globals.css` | Variables CSS (`:root`), import des polices, classes composants (`@layer components`) |
| `src/pages/Styleguide.tsx` | Démonstration vivante de chaque token et composant |
| `src/components/GothicMotif.tsx` | SVG de l'arche gothique en filigrane |
