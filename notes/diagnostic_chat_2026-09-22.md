# Diagnostic "le chat ne marche pas" (2026-09-22)

Tests faits dans un vrai navigateur (Chromium, Playwright) sur https://plaidia.vercel.app/app/chat, backend https://plaidia.onrender.com.

## Constats

1. **Le chat fonctionne** : un message court part, la réponse arrive en streaming (POST /api/chat/stream, 200).
2. **Refus intermittent (422) du garde-fou d'entrée** : le même message "Rédige une analyse très détaillée et longue (au moins 900 mots) de l'article 1240 du Code civil." a été refusé 2 fois sur 6 avec le motif "Tentative de contournement du système : vous demandez directement à l'IA (« Rédige »)...". Faux positif : le garde-fou (`backend/app/security_guard.py`, appel Claude, actif car `demo_mode: false`) est non déterministe. Côté interface, l'utilisateur voit la bulle disparaître et un toast d'erreur.
3. **Backend Render en retard sur l'interface** : 404 sur `GET /api/veille/notifications` et `GET /api/generations/` (les routeurs `veille.py` et `generations.py` existent dans le dépôt mais pas sur le serveur déployé). Le backend n'a donc pas été redéployé depuis les derniers commits.
4. **Serveur toujours en `demo_mode: false`** : clé API réelle active sur un lien public.
5. **Correctif de défilement validé en réel** (bundle déployé sur Vercel) : réponse remontée à `scrollTop = 0`, la vue ne bouge plus pendant que `scrollHeight` passe de 638 à 1316, bouton "Nouveau contenu" visible, clic = retour en bas.

## À faire

- Redéployer Render sur le dernier commit (Manual Deploy > Deploy latest commit), puis vérifier `/api/veille/notifications` et `/api/generations/`
- Passer Render en `DEMO_MODE=true` sans `ANTHROPIC_API_KEY` (le garde-fou LLM ne tourne alors plus et le chat répond avec les réponses préenregistrées)
- Décision à prendre sur les faux positifs du garde-fou si le mode réel est conservé : assouplir le prompt du garde-fou pour les formulations impératives légitimes ("Rédige", "Analyse", "Explique")
