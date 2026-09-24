# Correctif : défilement du chat pendant le streaming (2026-09-21)

## Cause

`frontend/src/pages/ChatPage.tsx` : un `useEffect` sur `chatHistorique` forçait `scrollTop = scrollHeight` à chaque fragment SSE reçu. Aucune détection de la position de l'utilisateur n'existait. `ChatContextuelPanel.tsx` a le même motif mais n'est pas en streaming, il n'est donc pas concerné.

## Correction

- `SEUIL_BAS_PX = 100` : l'utilisateur est "en bas" s'il est à 100 px ou moins du bas du fil
- `colleAuBasRef` : mis à jour par `onScroll` sur le conteneur du fil (`surDefilement`)
- Pendant le streaming : recalage en bas seulement si `colleAuBasRef` est vrai, sinon affichage du bouton flottant "↓ Nouveau contenu"
- Le bouton (`allerEnBas`) ou un nouvel envoi (`envoyerMessage`) ramènent en bas et masquent le bouton
- Hors streaming (chargement d'une conversation, nouvelle conversation) : comportement d'origine conservé (recalage en bas)
- Clé i18n `chatPage.nouveauContenu` ajoutée en FR et EN

Fichiers modifiés : `frontend/src/pages/ChatPage.tsx`, `frontend/src/i18n/locales/fr.json`, `frontend/src/i18n/locales/en.json`.

## Test manuel

1. `npm run dev` à la racine, ouvrir `/app/chat` avec une clé API réelle (le mode démo répond trop vite pour observer le streaming)
2. Envoyer une demande qui génère une longue réponse, par exemple "Rédige une analyse détaillée de l'article 1240 du Code civil, avec jurisprudence"
3. Pendant que ça écrit, remonter à la molette jusqu'au début de la réponse : la vue ne doit plus bouger et le bouton "↓ Nouveau contenu" apparaît en bas
4. Attendre la fin de la génération : la vue reste où elle est
5. Cliquer sur le bouton : retour en bas, bouton masqué
6. Cas de non-régression : rester en bas pendant une génération, la vue doit suivre le texte
7. Remonter, puis envoyer un nouveau message : retour en bas automatique
8. Remonter de moins de 100 px pendant la génération : la vue doit continuer à suivre

## Vérifications automatiques

`npx tsc --noEmit` sans erreur, `npx vitest run` : 12 fichiers, 64 tests passés. Pas de test automatisé ajouté pour ce comportement (jsdom ne calcule pas les dimensions de défilement).
