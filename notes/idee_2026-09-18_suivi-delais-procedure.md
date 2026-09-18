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

## Statut

Idée proposée, non implémentée. À valider avec l'utilisateur avant tout
développement.
