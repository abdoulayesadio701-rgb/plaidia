# Ce qui manque à Plaid'IA : avis (2026-09-22)

Basé sur ce que j'ai observé dans le code et sur le site en ligne. Classé par impact, deux angles : portfolio (convaincre un recruteur) et usage réel (avocats).

## 1. Aucune mesure de la fiabilité (impact portfolio : le plus fort)

Le cœur du projet est "anti-hallucination", mais rien ne le mesure. Aucun jeu d'évaluation dans le dépôt.
- Constaté en direct : le garde-fou a refusé à tort une demande normale 2 fois sur 6. Les tests existants simulent le modèle, ils ne l'auraient jamais vu
- À faire : un jeu de 30 à 50 questions juridiques avec réponse connue, et mesurer (a) le taux de citations inventées, (b) le taux de citations correctement balisées `[ART]` / `[VERIF]`, (c) le taux de faux refus du garde-fou, (d) ce que le vérificateur rattrape par rapport à l'agent principal seul
- Résultat : un tableau de chiffres à mettre en tête du README, CV et lettre ("réduit les citations non vérifiées de X % à Y %")

## 2. ~~Pas de CI~~ Réglé le 2026-09-22 (`.github/workflows/ci.yml`, badge dans le README, 3 jobs verts)

Pas de dossier `.github/workflows`. Les 333 tests backend et 64 tests front ne tournent que si on les lance à la main. Le bug Docker (2 modules non copiés) a fait échouer le déploiement Render sans que rien ne le signale avant.
- À faire : GitHub Actions avec pytest (racine et backend), `tsc --noEmit`, vitest, et un `docker build` du backend
- Ajoute aussi un badge "tests passing" dans le README

## 3. Pas de comptes ni d'isolation des données (impact usage réel : bloquant)

- Aucun système de comptes : la base SQLite est unique et partagée, sans `user_id`. Toute personne qui a le lien voit les dossiers de toutes les autres
- ~~La page de connexion (`ConnexionPage.tsx`) n'était pas reliée à une authentification~~ **Réglé le 2026-09-22 : page retirée** (l'adresse `/connexion` redirige vers la vitrine). Design récupérable avec `git show c83add4~:frontend/src/pages/ConnexionPage.tsx`
- Reste à faire : de vrais comptes (mots de passe hachés, JWT ou sessions, un `user_id` sur chaque table)
- En attendant, garder le mode démo (données non conservées) sur le lien public

## 4. Confidentialité et conformité (impact usage réel)

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
| 5 | Page confidentialité + anonymisation optionnelle | 1 à 2 jours | Réponse à l'objection n°1 d'un avocat |
| 6 | Vrais comptes et isolation des données | plusieurs jours | Passage de démo à produit |
