# Plaid'IA — API backend (FastAPI)

> Pour un déploiement public (Render + Vercel, Docker, variables
> d'environnement, domaine), voir [`DEPLOIEMENT.md`](../DEPLOIEMENT.md) à
> la racine du dépôt.

API REST + streaming SSE qui expose les fonctionnalités de Plaid'IA à un
front web séparé (React/Vite prévu). Elle ne réécrit **aucune** logique
métier : `analyse.py`, `db.py`, `recherche_juridique.py`, `judilibre.py`,
`extract.py` et `export.py`, à la racine du projet, sont importés tels
quels via `app/bootstrap.py` (ajout de la racine du projet à `sys.path`).

Conséquence directe : cette API et l'application tkinter (`gui.py`)
partagent **la même base SQLite** (`plaidoirie.db`, à la racine du projet)
et les mêmes fichiers de clés (`apikey.txt`, `judilibre_key.txt`,
`legifrance_creds.txt`) si vous les utilisez encore en plus des variables
d'environnement — les deux applications peuvent tourner en parallèle sans
conflit, elles lisent/écrivent le même dossier.

## Installation

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell : venv\Scripts\Activate.ps1)
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

## Configuration

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
```

Renseignez `ANTHROPIC_API_KEY` **et** `DEEPSEEK_API_KEY` dans `backend/.env`
pour un usage normal — la première pour les étapes de classification
(garde-fou, détection d'intention, notions juridiques, modèle Claude
Haiku), la seconde pour l'agent principal, le vérificateur, le critique et
le reste de la génération substantielle (DeepSeek). **Si l'une des deux
est absente** (et qu'aucun `apikey.txt`/`deepseek_apikey.txt` n'existe non
plus), le serveur bascule automatiquement en **mode démo** : voir la
section dédiée plus bas — c'est le mode pensé pour un déploiement public
partagé sur un CV ou avec des amis, sans exposer vos clés personnelles.
`JUDILIBRE_KEY_ID`
et `LEGIFRANCE_CLIENT_ID`/`LEGIFRANCE_CLIENT_SECRET` restent optionnels
dans tous les cas : sans eux, les routes `/api/jurisprudence/*` qui en
dépendent renverront une erreur 500 explicite
(`{"detail": "Erreur de configuration serveur : ..."}`) plutôt que de
planter silencieusement.

`backend/.env` n'est jamais lu par erreur par `gui.py`/`cli.py` (qui
utilisent `.env` à la racine ou les fichiers `.txt`) — les deux
configurations sont indépendantes, même si elles peuvent contenir les
mêmes valeurs.

## Lancement

Depuis le dossier `backend/` (important : le module s'appelle `app.main`) :

```bash
uvicorn app.main:app --reload --port 8000
```

L'API est alors disponible sur `http://localhost:8000`.

Vérification rapide :

```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"plaidia-api"}
```

## Documentation interactive (Swagger)

Une fois lancée : **http://localhost:8000/docs** (Swagger UI, généré
automatiquement par FastAPI à partir des schémas Pydantic) et
**http://localhost:8000/redoc** (ReDoc, lecture seule, plus lisible pour
une vue d'ensemble).

## Structure

```
backend/
  app/
    bootstrap.py     # ajoute la racine du projet à sys.path (import des modules legacy)
    deps.py          # get_dossier_or_404, construire_contexte_dossier (reproduit gui.py._contexte_dossier)
    main.py          # app FastAPI, CORS, gestion d'erreurs, montage des routers
    schemas/         # modèles Pydantic (1 fichier par domaine fonctionnel)
    routers/         # 1 fichier par préfixe /api/... — appelle directement analyse.py/db.py/...
  requirements.txt
  .env.example
  README.md
```

## Routes exposées

| Préfixe | Domaine | Détail |
|---|---|---|
| `/api/dossiers` | CRUD dossiers, recherche, import de documents (upload multipart), export Word des faits bruts | `dossiers.py` |
| `/api/analyse` | Conclusions adverses, résumé, plan de plaidoirie, simulateur d'objections, rapport complet, analyse stylistique, export Word/PDF | `analyse.py` |
| `/api/jurisprudence` | Consultation (Légifrance/Judilibre live ou corpus multi-source), collecte Judilibre, validation/rejet, corpus (OHADA, UE...), juridiction active | `jurisprudence.py` |
| `/api/notes` | Notes structurées par dossier, note client (rédaction + export) | `notes.py` |
| `/api/greffier` | Chronologie, extraction d'éléments clés, classement de document, contrôle de cohérence, recherche transversale, PV d'audience, vérification procédurale, réquisitoire, rapport d'instruction | `greffier.py` |
| `/api/chat` | Chat multi-tours **en streaming SSE** (`POST /api/chat/stream`) + persistance des conversations | `chat.py` |
| `/api/intention` | Interprétation d'une commande en langage naturel | `intention.py` |
| `/api/health` | Ping de santé | `main.py` |
| `/api/config` | État public (mode démo actif ? dossier de démo ? limite de caractères ?), lu par le front au démarrage | `main.py` |

Le détail complet (paramètres, schémas de réponse) est dans Swagger
(`/docs`) — c'est la référence à jour, générée directement depuis le code.

## Le marqueur "À VÉRIFIER"

Conservé tel quel, sans aucun traitement serveur, dans tous les champs
texte retournés (`resume`, `fondement`, `reponse`, fragments du chat...).
C'est au front de le repérer (recherche de sous-chaîne, comme le faisait
`gui.py._afficher()`) et de le surligner visuellement — c'est le
garde-fou anti-hallucination visible de l'outil, il ne doit jamais être
supprimé ni modifié côté serveur.

## Gestion des erreurs

Toute erreur renvoie un JSON `{"detail": "..."}` (`main.py` traduit les
exceptions Python natives des modules réutilisés — `EnvironmentError`,
`ValueError`, `FileNotFoundError`, `ImportError`, et un filet générique
`Exception` — en réponses JSON propres, jamais une trace Python brute).

**Exception** : `POST /api/chat/stream` répond en streaming SSE avec un
code HTTP 200 dès la première trame ; une erreur survenant en cours de
génération ne peut donc plus changer le code de statut HTTP — elle est
transmise comme un événement `event: error` avec `data: {"detail": "..."}`
(voir le format des événements SSE ci-dessous).

## Format du streaming SSE (`POST /api/chat/stream`)

Réponse `Content-Type: text/event-stream`, événements nommés :

- `event: recherche_debut` — émis uniquement si `recherche_live: true`, avant l'appel à Légifrance/Judilibre.
- `event: recherche_resultat` — `{"n_articles": N, "n_jurisprudence": M}`, une fois la recherche live terminée.
- `event: delta` — `{"text": "..."}`, un fragment de la réponse à la fois (peut contenir un morceau de `À VÉRIFIER` coupé entre deux trames — au front de bufferiser comme le faisait `_envoyer_message_chat` dans gui.py s'il veut un surlignage parfait).
- `event: done` — `{}`, fin normale du flux.
- `event: error` — `{"detail": "..."}`, en cas d'erreur pendant la génération.

## Mode démo (déploiement public — CV, portfolio)

Activé automatiquement si `ANTHROPIC_API_KEY` **ou** `DEEPSEEK_API_KEY`
(et leurs fichiers `apikey.txt`/`deepseek_apikey.txt` respectifs) sont
absents, ou explicitement via `DEMO_MODE=true` dans `.env`. Voir
`app/demo.py` et `app/demo_data.py`.

- **Réponses préenregistrées réalistes** pour les actions les plus
  démonstratives (analyser des conclusions, résumé, plan de plaidoirie,
  simulateur d'objections, rapport complet, chronologie, chat) sur un
  dossier fictif de droit du travail créé automatiquement. Le reste des
  actions IA renvoie une **503** explicite invitant à essayer ces
  actions-là ou à fournir sa propre clé.
- **`DEMO_RESET_DB`** (`true` par défaut dès que le mode démo est actif) :
  la base de données est entièrement vidée et reconstruite à **chaque
  démarrage** du serveur avant d'être réensemencée avec le seul dossier de
  démonstration — c'est ce qui rend vraie la mention "données non
  conservées en mode démo" affichée dans l'app.
  **⚠️ Ne mettez JAMAIS `DEMO_MODE=true` sur une base contenant des
  données à conserver sans avoir explicitement positionné
  `DEMO_RESET_DB=false`** : la perte de données serait immédiate et
  définitive au prochain redémarrage.
- **"Utiliser ma propre clé Anthropic"** : un visiteur peut fournir sa
  propre clé via l'en-tête `X-Anthropic-Api-Key` (jamais dans le corps, ni
  dans l'URL). Un middleware (`main.py::cle_api_personnelle_middleware`)
  la pose pour la durée de la requête via un `ContextVar` dans
  `analyse.py`, jamais journalisée ni écrite sur disque. Une clé
  personnelle fait sortir CETTE requête du mode démo sans rien changer
  pour les autres visiteurs.

## Protection anti-abus

- **Débit par IP** (`slowapi`) : `RATE_LIMIT_DEFAUT` (défaut `60/minute`),
  appliqué globalement via `SlowAPIMiddleware` — une IP qui dépasse la
  limite reçoit `429 {"detail": "Trop de requêtes..."}`.
- **Taille maximale des textes envoyés** : `MAX_TEXTE_CARACTERES` (défaut
  `50000`), appliqué comme `max_length` sur les champs texte libres des
  schémas Pydantic (conclusions, notes, corpus, questions...) — dépasser
  la limite renvoie une `422` de validation standard.

## CORS

Origines autorisées via `CORS_ORIGINS` dans `.env` (liste séparée par des
virgules). Par défaut : `http://localhost:5173` (Vite) et
`http://localhost:3000`. Ajoutez l'URL de votre front déployé avant la
mise en ligne.
