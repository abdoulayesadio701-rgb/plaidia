# Barre de tâches — audit et implémentation

Audit complet puis implémentation en 4 étapes validées d'une véritable
barre de tâches : centre de navigation, d'organisation et de contrôle du
travail juridique.

## Ce qui existait déjà (audité avant toute modification)

- **Dossier actif** : `useAppStore.dossierActifId` + `useDossierActif()` — déjà acquis.
- **Édition contextuelle par l'IA** : `ChatContextuelPanel` + `chat_actions.py` (le modèle propose un patch, le code le valide avant application) — déjà acquis sur 13 pages.
- **Recherche transversale** : `db.rechercher_dans_dossiers` (faits/parties/nom/domaine/analyses) — déjà acquis, pas encore exposé en dehors d'une page dédiée.
- **Historique de conclusions** : la table `analyses` gardait déjà une ligne par génération, mais seulement pour cette fonctionnalité.
- **Rien** pour : épinglage, tâches, versions de document, notifications persistantes, cycle de vie de document. Le chat `conversations_chat` n'était pas relié à un `dossier_id`. Aucune persistance côté client (état perdu au rafraîchissement).

## Scope MVP retenu (4 étapes, dans l'ordre validé)

Volontairement laissés de côté : cycle de vie à 5 états sur toutes les
fonctionnalités, centre de notifications complet, tableau de tâches,
recherche plein-texte au-delà de l'existant.

### Étape 1 — Barre de tâches + Récents
`TaskBar.tsx` (raccourcis vers Accueil, Mes dossiers, Assistant — uniquement
des destinations réellement existantes) + `config/recents.ts` (historique de
navigation en `localStorage`, aucune nouvelle table backend) +
`hooks/useSuivreRecents.ts` + `RecentsPanel.tsx`.

### Étape 2 — Épinglage
Nouvelle table `elements_epingles` (`type` + `reference_id`, jamais une
copie du contenu). Portée limitée à `dossier` et `analyse` — les deux
seuls types ayant à la fois un identifiant stable en base et une UI réelle
pour les rouvrir. `PinButton.tsx`, `EpinglesPanel.tsx`,
`backend/app/routers/epingles.py`.

### Étape 3 — Recherche globale + Command Bar élargie
Aucun nouveau backend : réutilise `dossiersApi.rechercherDossiers` et
`RechercheDossierResultats` déjà existants. `RechercheGlobaleModal.tsx`,
ouverte depuis TaskBar ou Ctrl/Cmd+K. `CommandBar.tsx` élargie de 5 à 9
actions routées (le backend `interpreter_intention` les reconnaissait déjà).

### Étape 4 — Versioning sur l'édition contextuelle
Nouvelle table `versions_document`, branchée sur `chat_actions.appliquer_patch`
(le point où une nouvelle version naissait déjà, jamais conservée
jusqu'ici). Restaurer une version AJOUTE une nouvelle ligne plutôt que de
revenir en arrière — aucune suppression automatique. `VersionsHistorique.tsx`,
montée dans `ChatContextuelPanel`, donc généralisée aux 13 pages qui
l'utilisent sans code spécifique par page.

## Vérification

Chaque étape : `tsc --noEmit` + `vite build` propres, suite de tests
backend complète (99 tests + 15 racine à la fin), vérification en
navigateur réel (Playwright) avec captures d'écran, et pour l'étape 4 un
vrai appel API de bout en bout (édition réelle → version créée → affichée
comme version actuelle).

## Fichiers créés

Backend : `app/routers/epingles.py`, `app/schemas/epingles.py`,
`app/routers/versions.py`, `app/schemas/versions.py`,
`tests/test_epingles.py`, `tests/test_versions.py`.

Frontend : `config/recents.ts`, `hooks/useSuivreRecents.ts`,
`layout/TaskBar.tsx`, `layout/RecentsPanel.tsx`, `layout/EpinglesPanel.tsx`,
`components/PinButton.tsx`, `components/RechercheGlobaleModal.tsx`,
`components/chat/VersionsHistorique.tsx`, `api/epingles.ts`, `api/versions.ts`.

## Recommandations pour la suite

- Étendre l'épinglage aux plans/simulateurs/conversations une fois qu'ils
  ont eux-mêmes une persistance et une UI de navigation dédiée.
- Réorganisation manuelle des éléments épinglés (glisser-déposer) — non
  fait, tri par date de création seulement pour l'instant.
- Notifications persistantes (au-delà des toasts éphémères actuels).
- Tableau de tâches lié à un dossier.
- Relier `conversations_chat` à `dossier_id` en base pour permettre de les
  épingler et de les retrouver par dossier.
