# Ce qui manque à Plaid'IA : avis (2026-09-22)

Basé sur ce que j'ai observé dans le code et sur le site en ligne. Classé par impact, deux angles : portfolio (convaincre un recruteur) et usage réel (avocats).

## 1. ~~Aucune mesure de la fiabilité~~ Réglé le 2026-09-22 : jeu d'évaluation construit et exécuté

`evaluation/` : 25 demandes légitimes, 11 attaques, 20 questions de fond, 13 questions-pièges. Run réel (381 appels, 2,89 $), revue manuelle sur Légifrance. Résultat : 98 % des citations exactes, 0 % des sources fictives adoptées, 0 % de faux refus après correction. Détail : `evaluation/resultats/2026-09-22_09h15/RESULTATS.md`.
- Limite trouvée et documentée : sans corpus de sources (chat simple), le vérificateur marque à tort 55 % des citations réelles comme "non vérifiées" — sur-prudence, pas une faille

## 2. ~~Pas de CI~~ Réglé le 2026-09-22 (`.github/workflows/ci.yml`, badge dans le README, 3 jobs verts)

Pas de dossier `.github/workflows`. Les 333 tests backend et 64 tests front ne tournent que si on les lance à la main. Le bug Docker (2 modules non copiés) a fait échouer le déploiement Render sans que rien ne le signale avant.
- À faire : GitHub Actions avec pytest (racine et backend), `tsc --noEmit`, vitest, et un `docker build` du backend
- Ajoute aussi un badge "tests passing" dans le README

## 3. Pas de comptes ni d'isolation des données (impact usage réel : bloquant)

- Aucun système de comptes : la base SQLite est unique et partagée, sans `user_id`. Toute personne qui a le lien voit les dossiers de toutes les autres
- ~~La page de connexion (`ConnexionPage.tsx`) n'était pas reliée à une authentification~~ **Réglé le 2026-09-22 : page retirée** (l'adresse `/connexion` redirige vers la vitrine). Design récupérable : `git log --diff-filter=D --format=%h -1 -- frontend/src/pages/ConnexionPage.tsx` donne le commit de suppression `<h>`, puis `git show <h>~:frontend/src/pages/ConnexionPage.tsx`
- Reste à faire : de vrais comptes (mots de passe hachés, JWT ou sessions, un `user_id` sur chaque table)
- En attendant, garder le mode démo (données non conservées) sur le lien public

## 4. ~~Confidentialité et conformité~~ Réglé le 2026-09-22 : page `/confidentialite` et anonymisation optionnelle

Page légale (liée depuis le footer de la landing et depuis Paramètres > À propos) : quelles données partent vers quel fournisseur, mode démo, clé personnelle, jurisprudence, limites du projet.
- **Anonymisation optionnelle** sur « Analyser des conclusions adverses » (`anonymisation.py`) : détection locale (aucun appel externe) des noms de personnes, pseudonymisation avant tout appel au modèle (garde-fou, agent, vérificateur, critique inclus), résultat affiché et enregistré avec les vrais noms. 19 tests dédiés + 6 tests d'intégration prouvant qu'aucun vrai nom ne fuit vers le modèle.

Des avocats manipulent des données couvertes par le secret professionnel, envoyées à un fournisseur américain (Anthropic, et éventuellement NVIDIA/DeepSeek). Le dépôt ne mentionne ni RGPD, ni politique de confidentialité, ni où vont les données.
- À faire : une page "Confidentialité" (quelles données partent, vers quel fournisseur, durée de conservation), une mention claire avant l'envoi d'un document, et une option d'anonymisation des noms avant appel au modèle (extension naturelle du projet, très valorisable en NLP)

## 5. Exploitation en production

- Pas de suivi d'erreurs ni de monitoring (Sentry ou équivalent)
- Pas de mesure réelle de coût par fonction (le rapport d'optimisation le reconnaît : estimations basées sur la structure du code, pas sur des tokens mesurés)
- Base SQLite sur disque éphémère (Render gratuit) : acceptable en démo, à remplacer par Postgres avec de vraies données
- Serveur gratuit qui s'endort : premier chargement de 30 à 60 s

## 6. Détails restants

- Captures d'écran et GIF absents du README
- Bundle front supérieur à 500 kB (chargement paresseux des pages peu visitées)
- Couverture de tests backend volontairement minimale (routes CRUD, exports Word/PDF)
- ~~`DEMO_MODE` à `false` sur le serveur en ligne~~ Réglé le 2026-09-22 : mode démo actif

## Ordre conseillé

| # | Action | Effort | Gain |
|---|---|---|---|
| 1 | ~~Passer `DEMO_MODE=true` sur Render~~ fait | 2 min | Protège ton crédit |
| 2 | ~~CI GitHub Actions~~ fait | 1 h | Crédibilité, évite un nouveau bug Docker |
| 3 | ~~Retirer la fausse page de connexion~~ fait | 30 min | Évite une fausse impression de sécurité |
| 4 | Jeu d'évaluation anti-hallucination avec chiffres | 1 à 2 jours | Le meilleur argument du portfolio |
| 5 | ~~Page confidentialité + anonymisation optionnelle~~ fait | 1 à 2 jours | Réponse à l'objection n°1 d'un avocat |
| 6 | Vrais comptes et isolation des données | plusieurs jours | Passage de démo à produit |
