# Lien de démo Plaid'IA : quoi faire et où le placer (2026-09-19)

Le guide complet de déploiement existe déjà : `DEPLOIEMENT.md` (à la racine). Ce fichier ne le remplace pas, il indique l'ordre des actions et où mettre le lien ensuite.

## État actuel

- Dépôt GitHub à jour : https://github.com/abdoulayesadio701-rgb/plaidia (branche `main` synchronisée)
- Secrets non versionnés (vérifié) : `apikey.txt`, `judilibre_key.txt`, `legifrance_creds.txt`, `plaidoirie.db` sont ignorés par git
- Fichiers de déploiement présents : `backend/Dockerfile`, `.dockerignore`, `render.yaml`, `frontend/vercel.json`
- **Pas encore déployé** : le README contient encore `https://<à-compléter>.vercel.app`

## Ce que tu dois faire toi-même (comptes personnels requis)

1. **Render** (backend) : New + > Blueprint > dépôt `plaidia`. Laisse `DEMO_MODE=true`, ne mets PAS `ANTHROPIC_API_KEY`. Note l'URL (ex. `https://plaidia-api.onrender.com`)
2. **Vercel** (frontend) : New Project > dépôt `plaidia`, Root Directory = `frontend`, variable `VITE_API_URL` = URL Render sans `/` final. Project Name = `plaidia` (sinon `plaidia-avocat`, etc.)
3. **Render** > Environment : `CORS_ORIGINS` = URL Vercel exacte, sauvegarder
4. **Test** en navigation privée : ouvrir l'URL, cliquer "Essayer la démo", lancer une analyse, vérifier le bandeau "Mode démo"

## Précautions pour un lien public

- **Mode démo obligatoire** : sans clé API côté serveur, personne ne peut consommer ton crédit Anthropic. Ne mets jamais ta clé dans les variables du déploiement public
- **Réveil lent** : le plan gratuit Render s'endort après 15 min. Ouvre le lien 1 minute avant un entretien ou avant d'envoyer une candidature, sinon le premier chargement dure 30 à 60 s
- **Base réinitialisée** à chaque réveil (voulu, annoncé dans l'app)
- Écris dans le CV "démo en ligne" et pas "en production"

## Où placer le lien une fois obtenu

Remplace `URL_DEMO` par l'URL Vercel réelle.

| Support | Formulation |
|---|---|
| **CV** (en-tête du projet) | `Plaid'IA | Démo : URL_DEMO | Code : github.com/abdoulayesadio701-rgb/plaidia` |
| **CV** (lien cliquable) | mets le lien en hypertexte sur le mot "Démo", et écris aussi l'URL en clair pour les versions imprimées ou lues par un ATS |
| **Lettre de motivation** | "Une démo en ligne est accessible sans inscription : URL_DEMO (cliquer sur « Essayer la démo »). Le code est sur GitHub." |
| **Portfolio** | bouton "Voir la démo" en haut de l'étude de cas, plus un bouton "Code source" ; ajoute la note "premier chargement possiblement lent (hébergement gratuit)" |
| **README.md** | remplacer les 2 occurrences de `https://<à-compléter>.vercel.app` (section Déploiement + résumé anglais), plus la ligne "Démo en ligne : à compléter" en haut |
| **LinkedIn** | section "Projets" et "En vedette", avec le lien démo |

## Astuces

- Un **domaine court** est plus propre sur un CV : `plaidia.vercel.app`
- Ajoute la ligne "Pas d'inscription, données fictives, aucune clé API requise" à côté du lien : ça rassure le recruteur et le pousse à cliquer
- Une fois le lien en ligne, ajoute la capture d'écran `docs/screenshot-landing.png` au README
- Teste le lien depuis ton téléphone avant d'envoyer : les recruteurs ouvrent souvent depuis leur mobile
