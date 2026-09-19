# Audit des fonctions qui ne marchaient pas — 2026-09-19

Méthode : les 34 pages ont été exécutées dans un vrai navigateur (Chromium, mode
démo, instances isolées), avec remplissage des champs et clic sur l'action
principale ; puis 19 exports Word, l'import d'un .docx, le chat, l'assistant
contextuel, les fonctions de gestion (jurisprudence, corpus, conversations,
épingles, domaine, suppression, notes, statut, thème) et la barre de commande.
Contrôle statique des traductions : 813 clés utilisées, aucune manquante, parité
FR/EN complète.

## Pannes trouvées et corrigées

1. **13 fonctions renvoyaient une erreur 503 sur l'app en ligne** (mode démo, pas de
   clé API) : analyse stylistique, traduction, extraction, classement, cohérence,
   PV d'audience, réquisitoire, rapport d'instruction, prise de note, note client,
   vérification procédurale, consultation de jurisprudence, chat contextuel.
   Corrigé par `backend/app/demo_data_outils.py` : repérage simple du texte saisi
   (dates, parties, articles, formules d'atténuation, nature du document) quand
   c'est possible, exemple fictif sinon. Les résultats liés à un dossier restent
   persistés comme de vrais résultats.
2. **Collecte de jurisprudence : erreur 500 illisible** (« 400 Client Error ...
   sandbox-api.piste.gouv.fr ») sans clé Judilibre. En démo : trois décisions
   **fictives** (mention « fictive » dans la référence), sans appel réseau ni
   quota consommé, sans doublon en base.
3. **Barre de commande inopérante en démo** : elle répondait toujours « incertain »,
   y compris pour son propre exemple « établir un plan de 10 minutes ».
   Interprétation par mots-clés (14 actions, durée extraite pour le plan et
   l'entraînement). Elle ne connaissait de toute façon pas chronologie,
   vérification, délais, entraînement, bordereau : ajoutés (prompt réel et routes).
4. **Pas d'export Word sur « Analyser des conclusions » et « Résumer ce dossier »** :
   l'endpoint d'export des conclusions existait mais aucune page ne l'appelait ;
   celui du résumé n'existait pas (`POST /api/analyse/resume/export`). Sur
   « Analyser », le bouton est placé hors du bloc « enregistré », sinon il
   disparaissait en démo (résultat non persisté).
5. **Durée du plan perdue** : « plan de 10 minutes » ouvrait la page avec 15 si un
   plan existait déjà (la durée du plan enregistré écrasait celle demandée). Séparées :
   curseur = prochain plan, étiquette = plan affiché.
6. Bandeau de l'accueil : titre blanc illisible en thème clair (voile trop clair).
7. Test instable de parallélisation (chronomètre) : remplacé par un verrou.

## Vérifié sans défaut

33 pages sur 34 sans aucune erreur (la 34e signale seulement un toast de succès),
19 exports Word valides, import .docx ajouté aux faits, chat et conversations,
assistant contextuel, statut de document, épingles, création / modification /
suppression de dossier, corpus, validation / rejet de jurisprudence, notes, thème
clair / sombre, page d'accueil publique et bouton « Essayer la démo ».

## Non modifié, à savoir

- Le sélecteur de langue FR/EN n'existe que sur la page d'accueil publique : un
  commit antérieur l'a retiré exprès de l'application.
- Le mode démo ne conserve rien (réinitialisation de la base à chaque démarrage du
  serveur) ; le plan Render gratuit n'a pas de disque persistant.
- Les réponses démo sont des exemples : elles n'ont aucune valeur juridique. Le
  catalogue des délais de procédure reste à faire relire par un juriste.
- Le chemin RÉEL (avec clé personnelle) de chaque endpoint modifié est couvert par
  `backend/tests/test_chemin_reel.py` (analyseurs simulés, aucun appel modèle).

## Tests

Backend 331 (dont `test_demo_outils.py`, `test_chemin_reel.py`), front 61, `tsc` propre.
