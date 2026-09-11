<div align="center">

# Plaid'IA

**Assistant IA de préparation de plaidoirie — France & espace OHADA**

*Analyse de conclusions adverses, plan de plaidoirie chronométré, simulateur d'objections,
chronologie automatique, vérification procédurale — avec un garde-fou anti-hallucination
visible à chaque réponse.*

*Démo en ligne : à compléter après déploiement (voir [DEPLOIEMENT.md](DEPLOIEMENT.md))* · [Documentation API](backend/README.md)

</div>

---

> 🇬🇧 *An English summary follows the French documentation — see [English summary](#english-summary) below.*

## Aperçu

> 📸 *Capture d'écran à ajouter ici une fois le premier déploiement public
> effectué (voir [DEPLOIEMENT.md](DEPLOIEMENT.md)) — placez-la dans
> `docs/screenshot-landing.png` et remplacez ce paragraphe par
> `![Aperçu de la page d'accueil](docs/screenshot-landing.png)`.*

## Présentation

Plaid'IA est un outil d'aide à la préparation de dossiers, à destination
des avocats (espace **Avocat**) et des greffiers/magistrats (espace
**Greffier**). Il ne rend pas d'avis juridique et ne remplace pas
l'analyse d'un professionnel du droit — c'est un assistant de préparation,
pas un système de décision.

Le projet est né comme une application de bureau (Tkinter, voir `gui.py`
à la racine du dépôt) avant d'être exposée comme une API web (FastAPI)
consommée par un front séparé (React). Toute la logique métier — appels à
Claude, extraction de documents, export Word/PDF, recherche juridique —
vit dans les modules Python à la racine du dépôt et est **réutilisée telle
quelle** par le backend web, sans être dupliquée ni réécrite.

## Fonctionnalités

### Espace Avocat

| Section | Fonctionnalités |
|---|---|
| **Poser une question** | Chat juridique multi-tours en streaming, recherche live Légifrance/Judilibre optionnelle |
| **L'Arsenal** | Analyser des conclusions adverses (syllogisme juridique), résumer un dossier, générer un plan de plaidoirie chronométré, simuler les objections probables, rapport complet, analyse stylistique des conclusions adverses, vérification procédurale |
| **La Chemise** | Parcourir/rechercher tous les dossiers, fiche dossier + historique des analyses, import de documents par glisser-déposer |
| **Le Grimoire** | Consulter/collecter/valider la jurisprudence, gérer un corpus juridique multi-source (OHADA, UE, droit sénégalais...), régler la juridiction active |
| **Le Carnet** | Prise de note structurée par l'IA, timeline des notes, rédaction d'une note client en langage simple |

### Espace Greffier / Magistrat

Chronologie automatique d'une affaire, extraction d'éléments clés d'un
document, classement automatique, contrôle de cohérence entre documents,
recherche transversale dans toutes les affaires, rédaction de PV
d'audience, vérification procédurale, analyse de réquisitoire et de
rapport d'instruction.

## Garde-fous anti-hallucination

- **Balisage des références juridiques** : chaque prompt système impose au
  modèle d'encadrer toute référence juridique d'une balise structurée
  (`[ART:<numéro>:<code>]`, `[JURISPRUDENCE:<référence>]`) et, s'il n'est
  pas certain de la citer correctement, `[VERIF:<description>]` plutôt que
  de l'affirmer comme un fait établi — voir `analyse.REGLE_BALISAGE_CITATIONS`.
  Le front repère ces balises dans n'importe quel texte produit (chat en
  streaming inclus) et leur donne un rendu visuel dédié — voir
  `frontend/src/components/RichOutput.tsx`.
- **Syllogisme juridique imposé** : les prompts d'analyse de conclusions
  et de réponse au chat exigent explicitement l'enchaînement faits →
  problème de droit → règle applicable → application aux faits →
  conclusion, plutôt qu'une conclusion présentée sans justification
  traçable (voir `analyse.py`).
- **Jurisprudence jamais citée sans validation humaine** : toute référence
  collectée automatiquement (Judilibre) reste « en attente » tant qu'un
  avocat ne l'a pas validée manuellement — jamais utilisable en contexte
  avant ça (voir `db.py`, table `jurisprudence`).
- **Mode démo transparent** : sur un déploiement public sans clé API, les
  réponses préenregistrées sont clairement annoncées comme telles (bandeau
  "Mode démo"), jamais présentées comme une analyse réelle.

## Architecture

```
┌──────────────────────────┐            ┌───────────────────────────────┐
│   Frontend (Vercel)      │   HTTPS    │   Backend (Render)             │
│   React + Vite + TS      │───────────▶│   FastAPI (Python)             │
│   Tailwind · Zustand     │◀───────────│                                 │
│                          │  JSON/SSE  │   /api/dossiers                │
│   "/"      → Landing     │            │   /api/analyse                 │
│   "/app/*" → App (SPA)   │            │   /api/jurisprudence           │
└──────────────────────────┘            │   /api/notes                   │
                                         │   /api/greffier                │
                                         │   /api/chat   (streaming SSE)  │
                                         │   /api/intention               │
                                         │   /api/config                  │
                                         └────────────────┬────────────────┘
                                                           │
                             ┌─────────────────────────────┼─────────────────────────────┐
                             │                             │                             │
                   ┌─────────▼─────────┐         ┌─────────▼─────────┐         ┌─────────▼─────────┐
                   │ Modules métier     │         │ SQLite             │         │ API Anthropic      │
                   │ (racine du dépôt)  │         │ (plaidoirie.db)    │         │ Claude              │
                   │                    │         │                    │         │                     │
                   │ analyse.py         │         │ dossiers           │         │ ou réponses          │
                   │ db.py              │         │ analyses           │         │ préenregistrées      │
                   │ recherche_         │         │ notes              │         │ (mode démo, voir     │
                   │   juridique.py     │         │ jurisprudence      │         │ backend/app/demo.py) │
                   │ judilibre.py       │         │ corpus_juridique   │         └───────────────────────┘
                   │ extract.py         │         │ conversations_chat │
                   │ export.py          │         └────────────────────┘
                   │ legifrance.py      │
                   └────────────────────┘
```

`backend/app/bootstrap.py` ajoute la racine du dépôt à `sys.path` pour
importer ces modules sans les copier — un seul jeu de fichiers, jamais
deux versions à synchroniser entre l'ancienne app Tkinter et l'API web.

## Stack technique

| Composant | Techno |
|---|---|
| Backend | FastAPI, Pydantic v2, `slowapi` (débit par IP), SQLite |
| IA | API Anthropic (Claude) |
| Frontend | React 18, Vite, TypeScript, React Router, Zustand, Tailwind CSS |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |
| Déploiement | Docker (backend, Render/Railway), Vercel (frontend) |

## Installation locale

Prérequis : Python 3.11+, Node.js 18+.

```bash
git clone https://github.com/<votre-compte>/plaidia.git
cd plaidia
```

**Backend** (voir [backend/README.md](backend/README.md) pour le détail complet) :

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows — macOS/Linux : source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env       # macOS/Linux : cp .env.example .env
# Renseignez ANTHROPIC_API_KEY dans backend/.env, ou laissez vide pour
# démarrer directement en mode démo.
uvicorn app.main:app --reload --port 8000
```

**Frontend**, dans un second terminal :

```bash
cd frontend
npm install
copy .env.example .env       # macOS/Linux : cp .env.example .env
npm run dev
```

L'app est alors sur `http://localhost:5173`, l'API sur `http://localhost:8000/docs`.

**Ou en une seule commande**, une fois les deux installations ci-dessus
faites (venv Python activé + dépendances backend installées, `npm install`
fait dans `frontend/`) :

```bash
npm install   # une seule fois, à la racine (installe concurrently)
npm run dev   # lance backend (:8000) ET frontend (:5173) ensemble, Ctrl+C arrête les deux
```

Alternative avec `make` (macOS/Linux, ou Windows via WSL/Git Bash) :
`make install` puis `make dev`.

## Tests

```bash
# Backend (pytest, mode démo — n'appelle jamais l'API Anthropic ni la base réelle)
cd backend && pip install -r requirements-dev.txt && pytest

# Frontend (Vitest)
cd frontend && npm install && npm test
```

Ou les deux d'un coup depuis la racine : `npm run test` (voir `package.json`).

Voir la section "Ce qui reste imparfait" plus bas pour la portée exacte de
cette suite de tests — volontairement minimale, pas une couverture
exhaustive.

## Déploiement

Guide complet, pas à pas, avec Dockerfile, `render.yaml`, `vercel.json` et
la liste exacte des variables d'environnement : **[DEPLOIEMENT.md](DEPLOIEMENT.md)**.

**Lien de démo** : `https://<à-compléter>.vercel.app` — à mettre à jour ici
une fois le déploiement effectué.

## Limitations connues

Liste honnête, à date — voir la conversation de développement pour le
détail complet de chaque point :

- **Jamais compilé/exécuté en conditions réelles** : tout le frontend a
  été écrit et relu sans Node.js disponible dans l'environnement de
  développement. Un premier `npm install && npm run build` réel peut
  révéler des erreurs de type ou de compilation non détectées par simple
  lecture.
- **Tests frontend jamais exécutés** pour la même raison (voir
  `frontend/src/components/__tests__/RichOutput.test.tsx`) — écrits avec
  soin, mais pas encore validés par un vrai `npm test`.
- **Couverture de tests backend volontairement minimale** : couvre le
  mode démo (réponses cannées, blocage 503, limite de taille, bascule clé
  personnelle) mais pas les routes CRUD complètes, pas les exports
  Word/PDF, pas le déclenchement réel du débit limite (slowapi).
- **Barre latérale mobile** : repliée par défaut sous 768px (correctif de
  cette session), mais reste un panneau fixe, pas un tiroir superposable —
  encore un peu à l'étroit sur un très petit écran.
- **Historique des conversations de chat** : l'API et le client existent
  (`GET /api/chat/conversations`) mais aucun écran ne permet de les
  parcourir depuis l'interface — seule la conversation en cours est
  visible.
- **`render.yaml`/`railway.json`** validés comme YAML/JSON syntaxiquement
  corrects, pas contre le schéma réel de chaque plateforme (jamais testés
  sur un vrai compte) — une configuration manuelle de repli est documentée
  dans `DEPLOIEMENT.md` si l'import automatique échoue.
- **`docker build` jamais lancé réellement** (Docker indisponible en
  développement) — la structure de copie du `Dockerfile` a été reproduite
  et testée manuellement, mais pas le build Docker lui-même.
- **Pas de relecture orthographique exhaustive** du texte français sur
  l'ensemble de l'app (plusieurs dizaines de pages) — une recherche
  ciblée n'a trouvé aucun résidu d'anglais, mais une relecture ligne à
  ligne complète n'a pas été faite.

## Auteur

**Abdoulaye Sadio** — Projet portfolio, NLP / TAL (Traitement Automatique
des Langues).

- GitHub : [abdoulayesadio701-rgb](https://github.com/abdoulayesadio701-rgb)
- LinkedIn : [abdoulaye-sadio](https://www.linkedin.com/in/abdoulaye-sadio)

---

## English summary

**Plaid'IA** is an AI assistant for legal case preparation, built for two
audiences: **lawyers** (adverse-argument analysis with explicit legal
syllogism, timed pleading plans, objection simulation, procedural
deadline checks) and **court clerks/magistrates** (automatic case
timelines, document classification, cross-document consistency checks,
hearing minutes drafting).

**Anti-hallucination guardrails** are the core design principle: every
system prompt requires the model to wrap every legal citation in a
structured tag (`[ART:<number>:<code>]`, `[JURISPRUDENCE:<reference>]`)
and, when it isn't fully certain about one, `[VERIF:<description>]`
instead of stating it as an established fact — each tag rendered with
its own visual treatment everywhere in the UI, including live-streamed
chat responses. Automatically collected case law is never citable until
a human validates it. A transparent **demo mode** serves realistic
pre-recorded responses (no API key required, no real Claude calls) when
no API key is configured server-side, with a visible banner so nobody
mistakes a demo answer for a real one; visitors can optionally supply
their own Anthropic key (stored client-side only, in `sessionStorage`,
sent as a header, never logged server-side) to get live answers instead.

**Stack**: FastAPI + SQLite + Anthropic Claude on the backend (deployed as
a Docker image on Render), React + Vite + TypeScript + Tailwind + Zustand
on the frontend (deployed on Vercel). The backend reuses a set of
pre-existing Python modules (`analyse.py`, `db.py`, `extract.py`,
`export.py`...) from the project's original Tkinter desktop app without
rewriting them — see the architecture diagram above.

**Quick start**: `npm install && npm run dev` from the repo root (see
[package.json](package.json)) runs both the backend (`uvicorn`) and the
frontend (`vite`) concurrently. Full step-by-step setup, testing, and
deployment instructions are in the French sections above and in
[DEPLOIEMENT.md](DEPLOIEMENT.md) (deployment steps are language-neutral —
commands and file names read the same either way).

**Live demo**: `https://<to-fill-in>.vercel.app`

**Author**: Abdoulaye Sadio — portfolio project, NLP. GitHub:
[abdoulayesadio701-rgb](https://github.com/abdoulayesadio701-rgb) ·
LinkedIn: [abdoulaye-sadio](https://www.linkedin.com/in/abdoulaye-sadio).
