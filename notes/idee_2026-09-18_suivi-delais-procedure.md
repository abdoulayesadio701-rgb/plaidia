# Idée — Suivi automatique des délais de procédure (espace Greffier)

Date : 2026-09-18

## Constat

L'espace Greffier dispose déjà d'outils d'analyse ponctuelle : Chronologie
(reconstruction d'une suite d'événements à partir de pièces), Vérification
procédurale (contrôle de conformité), Extraction (dates, parties, décisions
en 5 blocs), Classement, Cohérence, PV d'audience. Mais aucun outil ne
calcule et ne surveille les **délais de procédure en cours** (appel,
opposition, prescription, mise en état, conclusions à échéance...), qui sont
pourtant au cœur du métier de greffier : un délai manqué a des conséquences
directes sur la validité d'un acte. Les dates sont déjà extraites
(Extraction, Chronologie) mais jamais transformées en échéances actionnables.

## Fonctionnalité proposée : « Suivi des délais »

Nouvelle page dans l'espace Greffier : `/greffier/delais`, avec un endpoint
`POST /api/greffier/delais` prenant en entrée le texte d'une ou plusieurs
pièces (jugement, acte de procédure...) plus, en option, le type de
procédure.

### Fonctionnement

1. **Détection** : l'IA identifie dans le texte les événements déclencheurs
   de délai (signification d'un jugement, notification, acte introductif...)
   et le type de délai applicable (ex. appel : 1 mois en matière civile),
   réutilise la même mécanique d'extraction de dates que `Extraction` et
   `Chronologie` (mêmes prompts/parsing, pas de nouvelle brique de
   compréhension à inventer).
2. **Calcul de l'échéance** : pour chaque délai détecté, calcul de la date
   limite (point de départ + durée légale), avec un état visuel (jauge
   `JaugeConfiance`-like réutilisée en "jours restants" : vert / orange /
   rouge selon l'urgence) plutôt qu'une simple liste.
3. **Rattachement au dossier** : si un dossier actif existe, les délais
   calculés sont enregistrés et réapparaissent sur la fiche du dossier
   (même pattern que `useDernierDocumentGenere` + `documents_generes`,
   feature="delais_procedure") ; sinon persistance locale comme les autres
   outils indépendants d'un dossier (`useBrouillonPersistant`).
4. **Export** : liste des délais exportable en Word (`exporter_texte_libre_word`,
   pattern déjà utilisé pour PV d'audience/cohérence), utile pour impression
   ou versement au dossier physique.
5. **Alerte optionnelle (V2, hors scope immédiat)** : un badge sur la liste
   des dossiers (déjà existante) indiquant "délai à échéance sous 7 jours" —
   nécessiterait de vérifier le mécanisme de badges/notifications déjà en
   place avant de le concevoir plus précisément.

### Pourquoi c'est cohérent avec l'existant

- Réutilise l'extraction de dates déjà fiable (Extraction, Chronologie) au
  lieu de réinventer un nouveau parseur de dates.
- Réutilise tous les patterns déjà en place : persistance dossier/local,
  export Word, jauge visuelle, suppression avec confirmation.
- Comble un vrai vide métier : c'est la tâche la plus critique et la plus
  répétitive d'un greffier (surveiller qu'aucun délai n'est dépassé), et
  aucun des 6 outils Greffier actuels ne la couvre.

### Effort estimé

Moyen : le calcul de délai légal (mapping type de procédure → durée) demande
une base de règles simples (constante, pas d'IA) en plus de la détection par
IA du point de départ ; le reste (page, export, persistance) est la
répétition directe de patterns déjà codés dans le projet.

## Implémentation (2026-09-18)

Implémentée dans une version volontairement resserrée par rapport à l'idée :

- **Calcul 100 % déterministe, sans IA** : le greffier choisit un type de
  délai dans un catalogue (8 délais : appel civil, opposition, appel de
  référé, pourvoi civil, appel prud'hommes, appel correctionnel, pourvoi
  pénal, recours administratif) et la date du point de départ. Une date
  limite doit être reproductible et vérifiable, pas générée. Règles
  appliquées : art. 640 à 642 CPC (jour de départ exclu, mois de quantième à
  quantième, jours francs, prorogation au premier jour ouvrable si samedi,
  dimanche ou férié).
- **Détection automatique du point de départ par IA : NON faite** (V2 à
  décider). Elle exigerait une clé API (aucun repli en mode démo) et ferait
  peser un risque d'erreur sur une donnée critique.
- **Non pris en compte** (signalé à l'écran et dans l'export Word) : délais
  de distance (art. 643 CPC), suspension, interruption, point de départ
  réel (signification / notification / prononcé).
- **À faire valider par un juriste** : durées et références du catalogue
  (`backend/app/delais.py`) ; elles n'ont pas été vérifiées sur Légifrance.
- Persistance : `documents_generes` (feature="delais"), donc rattaché au
  dossier, rechargé au montage, visible dans « Documents générés » et dans
  la recherche transversale. Export Word via `exporter_texte_libre_word`.

Fichiers : `backend/app/delais.py` (nouveau), `backend/app/schemas/greffier.py`,
`backend/app/routers/greffier.py` (`GET /api/greffier/delais/catalogue`,
`POST /api/greffier/delais`, `POST /api/greffier/delais/export`),
`backend/tests/test_delais.py` (nouveau, 15 tests),
`frontend/src/pages/greffier/DelaisPage.tsx` (nouveau),
`frontend/src/api/{greffier,types}.ts`, `frontend/src/router.tsx`,
`frontend/src/config/navigation.ts`,
`frontend/src/pages/chemise/HistoriqueDossierPage.tsx`, `fr.json` / `en.json`.

Vérifié : `tsc --noEmit` propre ; `pytest` backend 256/256 ; scénario réel
dans Chromium (Playwright, instances isolées) : calcul avec prorogation,
statut « dépassée », persistance après navigation, présence dans « Documents
générés » et dans la recherche transversale, export Word, suppression avec
confirmation, aucune erreur JS.

## Statut

**Implémentée (version calcul déterministe) et testée — 2026-09-18.**
Alerte « délai sous 7 jours » sur la liste des dossiers : non faite (V2).

## Mise à jour (2026-09-18, suite)

- **Alerte sur la liste des dossiers : faite.** `GET /api/dossiers/echeances`
  (dernier calcul de délais de chaque dossier, `db.derniers_delais_par_dossier`) ;
  la carte d'un dossier affiche « Échéance dans N jours » quand l'échéance est à
  7 jours ou moins (`SEUIL_ALERTE_JOURS`, `config/echeances.ts`) et « N échéances
  dépassées ». Toujours calculé, jamais généré par IA.
- **Détection du point de départ par IA : toujours non faite**, volontairement
  (une date limite doit rester vérifiable ; dépend d'une clé API, sans repli démo).
- **Catalogue des 8 délais : à faire relire par un juriste** (non vérifié sur
  Légifrance).
