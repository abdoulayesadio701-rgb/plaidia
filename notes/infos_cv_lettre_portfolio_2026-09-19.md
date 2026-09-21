# Plaid'IA : infos pour CV, lettre de motivation et portfolio (2026-09-19)

Chiffres vérifiés dans le dépôt le 2026-09-19. Ne cite que ce qui est vrai à la date où tu postules (voir "Points à vérifier avant d'envoyer").

## 1. Fiche d'identité du projet

- **Nom** : Plaid'IA, assistant IA de préparation de plaidoirie (France et espace OHADA)
- **Type** : projet personnel / portfolio, domaine NLP / TAL appliqué au juridique
- **Durée** : du 2026-09-05 au 2026-09-19 (15 jours), 109 commits
- **Rôle** : conception, développement complet (backend, frontend, IA, tests, déploiement), seul
- **Utilisateurs cibles** : avocats (espace Avocat) et greffiers / magistrats (espace Greffier)
- **Stack** : Python 3.11, FastAPI, Pydantic v2, SQLite, API Anthropic (Claude Sonnet et Haiku), React 18, TypeScript, Vite, Tailwind, Zustand, i18next, pytest, Vitest, Docker, Render, Vercel
- **Liens** : GitHub abdoulayesadio701-rgb, LinkedIn abdoulaye-sadio (démo en ligne à ajouter après déploiement)

## 2. Chiffres clés (à utiliser tels quels)

| Indicateur | Valeur |
|---|---|
| Code Python | environ 22 000 lignes (dont environ 11 000 pour l'API backend) |
| Code TypeScript / React | environ 17 000 lignes |
| Endpoints REST | environ 108, répartis en 16 routeurs |
| Pages de l'application | 34 |
| Appels LLM distincts | 32 (27 Sonnet, 5 Haiku) |
| Tests automatisés | environ 315 tests pytest + 64 tests Vitest |
| Internationalisation | FR / EN, 813 clés de traduction, parité complète |
| Exports | 19 types d'exports Word (plus PDF) |

## 3. Lignes pour le CV

### Version courte (2 à 3 lignes)

**Plaid'IA, assistant IA de préparation de plaidoirie** | Python, FastAPI, React, TypeScript, Claude API | 2026
- Conception et développement seul d'une application web full stack (API FastAPI de 108 endpoints, front React/TypeScript de 34 pages) pour avocats et greffiers, avec garde-fou anti-hallucination sur les citations juridiques
- Architecture multi-agents de vérification (vérificateur, contradicteur, validation finale) et garde-fou de sécurité en entrée, avec jurisprudence jamais citable sans validation humaine
- Suite de 380 tests (pytest, Vitest), déploiement Docker (Render) et Vercel, mode démo sans clé API

### Version détaillée (5 à 6 puces)

- Conçu une application d'aide à la préparation de dossiers juridiques (France et OHADA) : analyse de conclusions adverses en syllogisme, plan de plaidoirie chronométré, simulateur d'objections, chronologie automatique, vérification procédurale, suivi des délais
- Mis en place un **garde-fou anti-hallucination** : balisage obligatoire des références juridiques (`[ART]`, `[JURISPRUDENCE]`, `[VERIF]`), rendu visuel dédié côté front y compris en streaming SSE, jurisprudence collectée automatiquement bloquée "en attente" jusqu'à validation par un avocat
- Conçu une **architecture multi-agents** (compréhension, agent principal, vérificateur juridique, contradicteur, validation finale) avec séparation stricte sécurité / qualité et pattern "le modèle propose, le code dispose"
- Intégré des sources juridiques réelles (API Judilibre, Légifrance, corpus OHADA, UE, droit sénégalais) avec recherche contextuelle, cache et timeouts
- **Optimisé les coûts API** : audit des 32 appels LLM, routage Sonnet / Haiku selon la tâche, second fournisseur optionnel pour les tâches de structuration, pistes de prompt caching documentées
- Livré en production : API FastAPI (rate limiting par IP, clé API personnelle côté client), front React bilingue, Docker, CI de tests, mode démo transparent avec bandeau visible

### Compétences à lister sous le projet

Prompt engineering, LLM / API Claude, streaming SSE, architecture multi-agents, RAG léger (recherche contextuelle), FastAPI, React, TypeScript, tests automatisés, i18n, Docker, déploiement (Render, Vercel), audit et optimisation de coûts

## 4. Paragraphes pour la lettre de motivation

### Accroche projet (à insérer dans le corps de la lettre)

"Pour démontrer ma capacité à livrer un produit IA de bout en bout, j'ai conçu et développé seul Plaid'IA, un assistant de préparation de plaidoirie destiné aux avocats et aux greffiers. Le domaine juridique ne tolère pas l'approximation : j'ai donc fait de la fiabilité le cœur du projet, avec un balisage obligatoire de chaque citation, une vérification par plusieurs agents et l'impossibilité de citer une jurisprudence non validée par un humain."

### Ce que ce projet prouve (au choix selon l'offre)

- **Offre IA / NLP** : maîtrise du prompt engineering en contexte à risque, gestion des hallucinations, orchestration multi-agents, choix de modèles selon coût et qualité
- **Offre développeur full stack** : API REST typée, front React/TypeScript, streaming, i18n, tests des deux côtés, déploiement
- **Offre data / legaltech** : intégration de sources juridiques officielles (Judilibre, Légifrance), structuration de documents non structurés (conclusions, PV, réquisitoires)
- **Toute offre** : autonomie, capacité à cadrer, livrer et documenter, esprit critique (audit des pannes, liste honnête des limites)

### Phrase de conclusion possible

"Ce projet reflète ma façon de travailler : partir d'un vrai besoin métier, poser des garde-fous mesurables, tester, puis documenter honnêtement ce qui reste imparfait."

## 5. Présentation portfolio / README (angle "étude de cas")

**Titre** : Plaid'IA, un assistant IA juridique où la fiabilité passe avant la fluidité

1. **Problème** : les LLM inventent des articles et des arrêts, ce qui est inacceptable pour un avocat
2. **Solution** : trois couches de défense
   - Prompts qui imposent un syllogisme et des balises de citation (`[ART]`, `[JURISPRUDENCE]`, `[VERIF]`)
   - Pipeline multi-agents qui relit la réponse (vérificateur, contradicteur, validation) contre le corpus validé
   - Validation humaine obligatoire pour toute jurisprudence collectée
3. **Décisions d'architecture** : réutilisation du code métier de l'ancienne app Tkinter par l'API (aucune duplication), séparation sécurité / qualité, mode démo transparent, clé API personnelle jamais journalisée
4. **Coûts** : audit des 32 appels LLM, répartition Sonnet / Haiku, précédent documenté d'un passage à Haiku annulé après perte de profondeur des réponses (démarche empirique, pas dogmatique)
5. **Qualité** : audit navigateur des 34 pages et 19 exports Word, 13 fonctions en erreur 503 corrigées, parité FR / EN vérifiée
6. **Limites assumées** : couverture de tests backend volontairement minimale, bundle front supérieur à 500 kB, `docker build` jamais lancé en local

Captures d'écran conseillées : page d'accueil, une analyse de conclusions avec balises visibles, un bandeau "Mode démo", le tableau de bord d'un dossier, un export Word.

## 6. Points à vérifier avant d'envoyer

- **Lien de démo** : le README contient encore `https://<à-compléter>.vercel.app`. Ne mets "démo en ligne" dans le CV qu'après le déploiement réel (voir DEPLOIEMENT.md)
- **Captures d'écran** : le README attend `docs/screenshot-landing.png`, pas encore ajoutée
- **Dépôt GitHub** : vérifie qu'il est public, et que `apikey.txt`, `judilibre_key.txt`, `legifrance_creds.txt` et `plaidoirie.db` ne sont pas versionnés (clés à ne jamais exposer)
- **Rester honnête** : projet personnel, pas de vrais utilisateurs, pas de déploiement validé sur un vrai compte Render / Railway. Évite "en production" sans nuance ; préfère "déployable, avec mode démo public"
- **Chiffres** : "380 tests" = 315 pytest + 64 Vitest, décomptés par fonction de test (les tests paramétrés en exécutent davantage). Relance `pytest` et `npm test` avant d'annoncer un chiffre exact
- **Sonnet 4.6 dans le code** : le rapport de coûts cite `claude-sonnet-4-6` et `claude-haiku-4-5`, ne les cite pas comme "derniers modèles" sans vérifier
- **Avertissement métier** : l'outil ne donne pas d'avis juridique, c'est un assistant de préparation. Garde cette formulation, elle montre ta maturité sur le sujet
