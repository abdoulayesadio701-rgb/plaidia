# Images à mettre dans le portfolio Plaid'IA (2026-09-19)

Principe : une image doit prouver un point précis (fiabilité, architecture, produit fini). 6 à 8 images suffisent, dans cet ordre, du plus percutant au plus technique.

## Conseils de prise de vue

- Navigateur en fenêtre 1440 x 900, zoom 100 %, thème cohérent sur toutes les captures (tout clair ou tout sombre)
- Utilise le **mode démo** avec des données fictives : aucun nom réel, aucune clé API visible, pas de barre de favoris ni d'onglets perso
- Format PNG, largeur 1600 px minimum, poids inférieur à 500 ko (compresse avec squoosh.app ou tinypng.com)
- Nom de fichier explicite, à ranger dans `docs/` (le README attend `docs/screenshot-landing.png`)
- Ajoute une légende d'une ligne sous chaque image qui dit ce qu'elle prouve

## Les 8 images (par priorité)

### 1. Page d'accueil (héro du portfolio)
- **Page** : LandingPage (`/`)
- **Fichier** : `docs/01-landing.png`
- **Ce qu'elle prouve** : le produit est fini, pensé et soigné (identité gothique, motif de l'app)
- **Légende** : "Page d'accueil : deux espaces, Avocat et Greffier"

### 2. Garde-fou anti-hallucination en action (l'image la plus importante)
- **Page** : Arsenal > Analyser des conclusions (AnalyserConclusionsPage), ou le chat
- **Fichier** : `docs/02-balises-citations.png`
- **À cadrer** : un résultat où on voit à la fois une balise article `[ART]`, une jurisprudence et un `[VERIF]` avec leur rendu visuel distinct, plus le syllogisme (faits, problème de droit, règle, application, conclusion)
- **Ce qu'elle prouve** : ton point fort, la fiabilité juridique
- **Légende** : "Chaque citation est balisée, celles dont le modèle doute sont marquées à vérifier"

### 3. Panneau de vérification multi-agents
- **Composants** : VerificationPanel et EtapePipelineIndicator
- **Fichier** : `docs/03-verification-agents.png`
- **À cadrer** : le pipeline avec ses étapes (vérificateur, contradicteur, validation) et le bloc de vérification sous la réponse. Nécessite une clé API réelle ou personnelle, car il est absent en mode démo
- **Ce qu'elle prouve** : architecture multi-agents visible côté utilisateur
- **Légende** : "L'agent qui rédige n'est pas le seul juge de sa réponse"

### 4. Validation humaine de la jurisprudence
- **Page** : Grimoire > Gérer la jurisprudence (GererJurisprudencePage)
- **Fichier** : `docs/04-jurisprudence-en-attente.png`
- **À cadrer** : des décisions au statut "en attente" avec le bouton de validation
- **Ce qu'elle prouve** : un humain reste dans la boucle, aucune jurisprudence citée sans validation
- **Légende** : "Une décision collectée reste inutilisable tant qu'un avocat ne l'a pas validée"

### 5. Plan de plaidoirie chronométré et entraînement
- **Pages** : PlanPlaidoiriePage et EntrainementPage (avec chronomètre et historique)
- **Fichier** : `docs/05-plan-plaidoirie.png`
- **Ce qu'elle prouve** : fonctionnalité métier concrète, utile, différenciante
- **Légende** : "Plan de plaidoirie de 10 minutes et mode entraînement chronométré"

### 6. Tableau de bord d'un dossier
- **Page** : HomePage avec un dossier actif (échéances, pièces, analyses)
- **Fichier** : `docs/06-tableau-de-bord.png`
- **Ce qu'elle prouve** : produit complet, pas une simple démo de prompt
- **Légende** : "Tableau de bord du dossier actif : échéances, bordereau de pièces, historique"

### 7. Espace Greffier : chronologie automatique
- **Page** : ChronologiePage (ou VerificationProceduralePage / DelaisPage)
- **Fichier** : `docs/07-greffier-chronologie.png`
- **Ce qu'elle prouve** : deuxième public cible, structuration de documents non structurés (NLP)
- **Légende** : "Chronologie d'une affaire extraite automatiquement des pièces"

### 8. Schéma d'architecture (image non-capture, à créer)
- **Fichier** : `docs/08-architecture.png`
- **Contenu** : reprendre le schéma du README (Frontend Vercel, Backend Render FastAPI, modules métier, SQLite, API Claude ou mode démo), ajouté du pipeline multi-agents :
  Garde-fou d'entrée > Agent de compréhension > Agent principal > Vérificateur > Contradicteur > Validation finale
- **Outils** : Excalidraw, draw.io ou Figma, 2 couleurs maximum, texte lisible en miniature
- **Ce qu'elle prouve** : tu sais concevoir une architecture, pas seulement l'utiliser
- **Légende** : "Architecture : un seul jeu de modules métier partagé entre l'app de bureau et l'API web"

## Images optionnelles (si la place le permet)

- **Bandeau "Mode démo"** : montre la transparence (rien n'est présenté comme une vraie analyse). Petit crop suffit
- **Export Word ouvert dans Word** : preuve que les 19 exports produisent un vrai document (un fichier existe déjà dans `exports/`)
- **Barre de commande** : saisir "établir un plan de 10 minutes" et montrer l'interprétation (14 actions)
- **Sélecteur FR / EN** : interface bilingue
- **Terminal avec les tests au vert** : `pytest` et `npm test`, crédibilité qualité (cadre serré, police lisible)
- **GIF ou vidéo de 30 à 45 s** : question, réponse en streaming avec balises qui s'affichent, clic sur une jurisprudence. Plus convaincant que 8 images fixes (outils : ScreenToGif ou OBS)

## Ordre conseillé selon le support

| Support | Images à garder |
|---|---|
| README GitHub | 1, 2, 8 |
| Page portfolio (étude de cas) | 1, 2, 3, 4, 5, 8 |
| Post LinkedIn | GIF, ou 2 et 8 en carrousel |
| Dossier de candidature PDF | 2, 8 et une capture produit |

## À éviter

- Captures avec des vraies données de clients, des noms réels ou des clés API visibles
- Captures de pages vides ("aucun dossier") ou d'erreurs
- Trop d'images similaires : chaque image doit prouver quelque chose de différent
- Une capture du mode démo présentée comme une réponse réelle de Claude : précise-le dans la légende si c'est le cas
