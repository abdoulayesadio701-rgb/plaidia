# Déployer Plaid'IA — lien public stable

Guide pas à pas pour obtenir une URL publique gratuite et stable,
partageable sur un CV ou avec des amis, en mode démo (voir
`backend/README.md`).

## Le choix retenu : Render (backend) + Vercel (frontend)

| Option | Coût | Complexité | Verdict |
|---|---|---|---|
| **Render + Vercel** (retenu) | Gratuit | Deux services à connecter, mais chacun fait une seule chose | ✅ Le plus simple pour CETTE stack (API séparée + SPA Vite) |
| Railway (backend) + Vercel | Railway n'a plus de palier gratuit permanent depuis 2023 (crédit d'essai puis facturation) | Identique à Render | À éviter pour un lien "gratuit à long terme" |
| Tout-en-un dans un seul conteneur Docker | Gratuit (Render seul) | Plus complexe : il faut construire le frontend, servir les fichiers statiques ET l'API depuis le même processus FastAPI, avec un `Dockerfile` multi-étapes | ❌ Plus de travail pour un gain nul ici — Vercel fait déjà gratuitement, mieux et plus vite (CDN), ce qu'un conteneur unique referait à la main |

Séparer les deux a un autre avantage concret : un changement de design du
front se redéploie sur Vercel en ~30 secondes sans jamais redémarrer
l'API (donc sans jamais perdre les données du mode démo en cours de
session), et inversement.

`railway.json` est quand même fourni à la racine si vous préférez Railway
malgré tout (ex. crédit gratuit encore actif sur votre compte) — la
procédure est identique à Render, juste sur un tableau de bord différent.

## Fichiers déjà prêts dans ce dépôt

| Fichier | Rôle |
|---|---|
| `backend/Dockerfile` | Image du backend — build avec la racine du dépôt comme contexte |
| `.dockerignore` | Exclut secrets, base de données locale, artefacts de build du contexte Docker |
| `render.yaml` | Blueprint Render (détecté automatiquement) |
| `railway.json` | Config Railway équivalente, si vous préférez cette plateforme |
| `frontend/vercel.json` | Rewrites SPA (indispensable en React Router) + commande de build |
| `backend/.env.example` | Liste commentée de toutes les variables d'environnement backend |
| `frontend/.env.example` | Variable d'environnement frontend (`VITE_API_URL`) |

---

## Étape 0 — Mettre le dépôt sur GitHub

Ce projet n'est pas encore un dépôt git. Depuis la racine du projet :

```bash
git init
git add .
git status   # vérifiez qu'AUCUN fichier apikey.txt / judilibre_key.txt /
             # legifrance_creds.txt / *.db n'apparaît dans la liste --
             # le .gitignore déjà présent les exclut normalement
git commit -m "Initial commit"
```

Créez un dépôt vide sur [github.com/new](https://github.com/new) (nom
libre, ex. `plaidia`), puis :

```bash
git remote add origin https://github.com/<votre-compte>/plaidia.git
git branch -M main
git push -u origin main
```

## Étape 1 — Backend sur Render

1. Sur [render.com](https://render.com), connectez-vous avec GitHub.
2. **New +** → **Blueprint** → sélectionnez le dépôt `plaidia`. Render
   détecte `render.yaml` et propose de créer le service `plaidia-api`
   automatiquement (type Docker, plan Free). Validez.
   - Si vous préférez tout configurer à la main plutôt que via le
     Blueprint : **New +** → **Web Service** → votre dépôt → Runtime
     **Docker** → Dockerfile Path `backend/Dockerfile` → Docker Build
     Context Directory `.` (la racine, pas `backend`) → Plan **Free**.
3. Dans **Environment**, vérifiez/complétez les variables (voir tableau
   plus bas). `render.yaml` a déjà posé `DEMO_MODE=true`, `DEMO_RESET_DB=true`,
   `RATE_LIMIT_DEFAUT`, `MAX_TEXTE_CARACTERES` — rien à faire dessus.
4. **Create Web Service**. Premier build ≈ 3-5 minutes. Notez l'URL
   attribuée, du type `https://plaidia-api.onrender.com`.
5. Testez immédiatement :
   ```bash
   curl https://plaidia-api.onrender.com/api/health
   curl https://plaidia-api.onrender.com/api/config
   ```
   `config` doit répondre `"demo_mode": true` et un `dossier_demo_nom`.

⚠️ **Palier gratuit Render** : le service se met en veille après ~15 min
sans requête, et met 30-60 secondes à se réveiller à la requête suivante
(page qui semble "figée" le temps du réveil — normal, pas une panne).
C'est aussi ce qui purge la base à chaque réveil, cohérent avec la mention
"données non conservées en mode démo".

## Étape 2 — Frontend sur Vercel

1. Sur [vercel.com](https://vercel.com), connectez-vous avec GitHub.
2. **Add New** → **Project** → sélectionnez le dépôt `plaidia`.
3. **Root Directory** : cliquez *Edit* et choisissez `frontend` (le projet
   Vite n'est pas à la racine du dépôt). Vercel détecte automatiquement le
   framework "Vite" à partir de là.
4. **Environment Variables** → ajoutez :
   | Nom | Valeur |
   |---|---|
   | `VITE_API_URL` | `https://plaidia-api.onrender.com` (l'URL Render de l'étape 1, **sans** `/` final) |
5. **Deploy**. ~1 minute. Vercel attribue une URL du type
   `https://plaidia.vercel.app` (voir "Domaine" plus bas si ce nom précis
   est déjà pris).

Les variables `VITE_*` sont figées **au moment du build** (Vite les
intègre dans les fichiers JS statiques) — changer `VITE_API_URL` plus
tard exige de relancer un déploiement (Vercel → Deployments → ⋯ →
*Redeploy*), un simple redémarrage du service ne suffit pas.

## Étape 3 — Reboucler le CORS

Retournez sur Render → `plaidia-api` → **Environment** → modifiez
`CORS_ORIGINS` pour y mettre l'URL Vercel **réelle** obtenue à l'étape 2 :

```
CORS_ORIGINS=https://plaidia.vercel.app
```

Sauvegarder déclenche automatiquement un redéploiement du backend
(30 secondes). Sans cette étape, le navigateur bloquera les appels du
front vers l'API avec une erreur CORS dans la console.

## Étape 4 — Test de bout en bout

1. Ouvrez l'URL Vercel dans un navigateur en navigation privée (évite tout
   cache).
2. La page d'accueil publique doit s'afficher (voir `frontend/src/pages/LandingPage.tsx`).
3. Cliquez **Essayer la démo** → vous arrivez sur `/app/chemise/dossiers`
   avec le dossier fictif « Diallo c/ Atlas Logistique » déjà présent.
4. Ouvrez-le, lancez **Analyser des conclusions adverses** : la réponse
   doit apparaître en quelques secondes (préenregistrée, pas d'appel réel
   à Claude) et le bandeau **Mode démo** doit être visible en haut de
   l'app.
5. Si le tout premier chargement de l'étape 3 semble bloqué ~30-60 s, c'est
   le réveil du service Render gratuit (voir avertissement étape 1) — pas
   un bug.

---

## Variables d'environnement — liste exacte

### Render (backend)

| Variable | Valeur recommandée (déploiement public) | Obligatoire ? |
|---|---|---|
| `DEMO_MODE` | `true` | Recommandé sur un lien public partagé |
| `DEMO_RESET_DB` | `true` | Oui si `DEMO_MODE=true` (sinon la base grossit indéfiniment) |
| `CORS_ORIGINS` | `https://<votre-projet>.vercel.app` | Oui — sans ça, le front ne peut pas appeler l'API |
| `RATE_LIMIT_DEFAUT` | `60/minute` | Non (défaut déjà correct) |
| `MAX_TEXTE_CARACTERES` | `50000` | Non (défaut déjà correct) |
| `ANTHROPIC_API_KEY` | *(laisser vide pour rester en mode démo)* | Non — uniquement si vous voulez désactiver le mode démo sur ce déploiement public |
| `JUDILIBRE_KEY_ID`, `JUDILIBRE_ENV` | — | Non |
| `LEGIFRANCE_CLIENT_ID`, `LEGIFRANCE_CLIENT_SECRET`, `LEGIFRANCE_ENV` | — | Non |
| `PLAIDIA_DB_PATH` | ex. `/data/plaidoirie.db` | Non — seulement si vous montez un disque persistant (voir Persistance) |
| `PORT` | *(fixée automatiquement par Render, ne pas y toucher)* | — |

### Vercel (frontend)

| Variable | Valeur | Obligatoire ? |
|---|---|---|
| `VITE_API_URL` | `https://plaidia-api.onrender.com` (URL Render, sans `/` final) | Oui |

---

## Persistance : SQLite et volumes

En mode démo, la base est **volontairement** effacée et reconstruite à
chaque démarrage du conteneur (`DEMO_RESET_DB=true`, voir
`backend/app/main.py::lifespan` et `db.py::reinitialiser_donnees_demo`) —
c'est le comportement voulu, annoncé dans l'app ("données non conservées
en mode démo"), et le palier gratuit de Render n'offre de toute façon pas
de disque persistant.

**Si vous voulez conserver les données** (désactiver le mode démo, ou
garder un historique même en démo) :

1. Passez le service Render sur un plan payant (Starter et plus) — un
   disque persistant n'est pas disponible sur le plan Free.
2. Render → votre service → **Disks** → **Add Disk** : donnez-lui un nom,
   une taille (1 Go suffit largement pour du SQLite), et un point de
   montage, par exemple `/data`.
3. Ajoutez la variable d'environnement `PLAIDIA_DB_PATH=/data/plaidoirie.db`
   (voir `db.py`, qui lit cette variable pour placer la base ailleurs que
   son emplacement par défaut à côté du code).
4. Mettez `DEMO_RESET_DB=false` — sinon le disque persistant serait vidé
   à chaque redémarrage, ce qui annulerait l'intérêt de l'opération.

Sur Railway, l'équivalent s'appelle un **Volume** (Service → Settings →
Volumes → Add Volume, avec un point de montage comme `/data`) ; même
principe pour `PLAIDIA_DB_PATH` et `DEMO_RESET_DB`.

---

## Domaine gratuit et mention sur un CV

Vercel attribue automatiquement `https://<nom-du-projet>.vercel.app`. Pour
obtenir précisément `plaidia.vercel.app` :

- Lors de l'import du projet (étape 2), le champ **Project Name** est
  pré-rempli avec le nom du dépôt GitHub — mettez-le à `plaidia`. Si ce
  nom est déjà pris par quelqu'un d'autre sur Vercel (les sous-domaines
  `.vercel.app` sont uniques mondialement), essayez `plaidia-avocat`,
  `plaidia-demo` ou `plaidia-app`.
- Renommable après coup : Project → **Settings** → **General** → *Project
  Name* → Save. L'URL change immédiatement pour refléter le nouveau nom
  (pensez à remettre à jour `CORS_ORIGINS` sur Render si vous renommez
  après l'étape 3).

**Sur le CV** : un lien de portfolio se met simplement en clair, pas
besoin de raccourcisseur d'URL — par exemple dans une ligne dédiée sous
votre nom, ou dans la section "Projets" :

```
Plaid'IA — Assistant IA de préparation de plaidoirie (NLP/TAL)
https://plaidia.vercel.app
```

Sur LinkedIn, ce même lien peut être ajouté à la fois dans la section
**Coordonnées** (as "Site web / Portfolio") et dans un post ou la section
**Projets** du profil, avec la même URL.
