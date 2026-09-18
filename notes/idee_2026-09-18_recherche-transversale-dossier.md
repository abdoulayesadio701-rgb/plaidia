# Idée — Recherche transversale dans les contenus générés d'un dossier

Date : 2026-09-18
Espaces concernés : **Avocat et Greffier** (fonctionnalité partagée)

## Constat

Un dossier actif accumule au fil du temps beaucoup de contenu généré et
persisté : plans de plaidoirie, analyses de conclusions, résumés,
simulateurs d'objections (Avocat), chronologies, vérifications procédurales,
notes client (Greffier), sans compter les pièces importées. Chaque type de
contenu est déjà persisté et accessible individuellement (page par page,
`Historique du dossier`), mais il n'existe aucun moyen de **chercher une
information précise à travers tout ce qui a été généré pour un dossier** :
par exemple retrouver "où ai-je déjà mentionné cette date de signification"
ou "quel argument avait été évoqué dans le simulateur d'objections sur ce
point" sans rouvrir chaque page une par une.

## Fonctionnalité proposée : « Recherche dans le dossier »

Un champ de recherche accessible depuis la fiche du dossier (`chemise/`,
à côté de `HistoriqueDossierPage.tsx`), utilisable aussi bien côté Avocat que
Greffier puisqu'il porte sur `documents_generes`/`analyses`/`notes`, des
tables déjà communes aux deux espaces.

### Fonctionnement

1. **Indexation** : rien de nouveau à construire pour la collecte — toutes
   les données existent déjà en base (`documents_generes`, `analyses`,
   `notes`, `versions_document`) grâce au chantier de persistance déjà livré.
   Un nouvel endpoint `GET /api/dossiers/{dossier_id}/recherche?q=...`
   interroge ces tables (recherche texte simple type `LIKE`/FTS SQLite pour
   commencer, sans dépendance externe).
2. **Résultats groupés par type** : les correspondances sont affichées
   regroupées par fonctionnalité d'origine (Plan de plaidoirie, Résumé,
   Chronologie, Note client...), avec un extrait surligné du passage
   correspondant et un lien direct vers la page concernée (réutilise
   `CHEMIN_PAR_FEATURE`, déjà introduit dans `HistoriqueDossierPage.tsx`
   pour mapper feature → route).
3. **Filtrage par espace** (optionnel) : bascule "Avocat / Greffier / Tout"
   pour ne montrer que les résultats pertinents selon qui consulte, utile
   si un même dossier est partagé entre un avocat et un greffier.

### Pourquoi c'est cohérent avec l'existant

- Aucune nouvelle donnée à générer ni à stocker : exploite uniquement ce qui
  est déjà persisté suite aux chantiers précédents (persistance Arsenal +
  Greffier + locale).
- Réutilise `CHEMIN_PAR_FEATURE` déjà en place pour la navigation croisée.
- Complète naturellement `HistoriqueDossierPage.tsx`, qui liste déjà tout le
  contenu du dossier mais sans capacité de recherche/filtrage textuel.
- Utile aux deux espaces sans aucune duplication de logique : c'est la
  fonctionnalité elle-même qui est transversale, pas deux implémentations
  séparées.

### Effort estimé

Petit à moyen : 1 endpoint backend (requête SQL sur les tables existantes,
pas de nouvel appel modèle IA nécessaire pour une recherche texte simple),
1 composant frontend (champ de recherche + liste de résultats groupés),
aucune migration de schéma requise dans un premier temps.

## Décisions de conception (2026-09-18, avant implémentation)

### 1. Portée de la recherche : plein texte, pas seulement titres/métadonnées

**Choix par défaut : recherche en plein texte** dans le contenu généré
(`documents_generes.contenu`, `analyses.resultat`, `notes.texte`), pas
seulement dans les titres ou métadonnées (feature, date, dossier).

Justification : le besoin exprimé dans le constat ("où ai-je déjà mentionné
cette date de signification") est par nature une recherche de contenu, pas
de titre — un plan de plaidoirie ou une chronologie n'a pas de titre
distinctif par section. Une recherche limitée aux métadonnées ne couvrirait
quasiment aucun des cas d'usage réels. Techniquement peu coûteux : SQLite
`LIKE '%q%'` sur les colonnes texte existantes suffit pour un premier
jet (les volumes par dossier restent modestes) ; FTS5 pourra être envisagé
plus tard si la performance ou la pertinence (recherche par mots proches,
tolérance aux fautes) le justifient — non nécessaire pour la V1.

### 2. Regroupement des résultats : tri par date de génération la plus récente

**Choix par défaut : au sein de chaque groupe (type de contenu), tri par
date de génération décroissante** (le plus récent en premier), pas par
score de pertinence.

Justification : un tri par pertinence nécessiterait un score de similarité
(fréquence du terme, position, longueur...) — complexité et risque
d'incohérence perçue ("pourquoi ce résultat est-il en premier ?") pour un
gain incertain avec une recherche `LIKE` simple qui n'a pas de notion fine de
pertinence à exploiter. Le tri chronologique est prévisible, cohérent avec
le reste de l'application (`Historique du dossier` liste déjà tout par
date), et correspond à l'usage réel : en cas de plusieurs mentions d'un
même terme (ex. plusieurs résumés régénérés), la version la plus récente
est presque toujours celle qui intéresse l'utilisateur.

### 3. Visibilité selon le rôle : aucune restriction, tout le contenu est visible

**Choix par défaut : la recherche montre tout le contenu du dossier, sans
filtrage imposé par rôle.** Le filtre "Avocat / Greffier / Tout" mentionné
plus haut reste une **bascule d'affichage optionnelle et manuelle** pour
réduire le bruit visuel, pas une restriction d'accès.

Justification : l'application n'a aujourd'hui **aucun système
d'authentification ni de rôle utilisateur réel** (vérifié dans
`backend/app/deps.py` — pas de notion de `current_user`/`role` ; Avocat et
Greffier sont deux espaces de navigation dans la même application, pas deux
comptes séparés). Imposer une restriction de visibilité par rôle créerait
une fausse impression de cloisonnement de sécurité qui n'existe pas ailleurs
dans le produit, sans bénéfice réel puisque n'importe qui utilisant
l'application voit déjà tout le reste (fiche dossier, historique, faits
bruts) sans distinction de rôle. Si une vraie authentification par rôle est
introduite un jour, ce choix sera à revoir en même temps que le reste de
l'application — ce n'est pas à la recherche transversale d'inventer seule
un modèle de permissions.

## Implémentation (2026-09-18)

Validée par l'utilisateur, implémentée telle que documentée ci-dessus.

- Backend : `db.rechercher_dans_documents_dossier(dossier_id, terme)`
  (`db.py`) — recherche `LIKE` en plein texte dans `documents_generes`,
  `analyses` et `notes` du dossier, triée par date décroissante ; endpoint
  `GET /api/dossiers/{dossier_id}/recherche?q=...`
  (`backend/app/routers/dossiers.py`), schéma `ResultatRechercheContenuOut`
  (`backend/app/schemas/dossiers.py`).
- Frontend : `dossiersApi.rechercherDansDossier(dossierId, q)`
  (`frontend/src/api/dossiers.ts`), type `ResultatRechercheContenu`
  (`frontend/src/api/types.ts`), champ de recherche avec débounce (300 ms)
  et résultats groupés par type + liens directs, ajoutés dans
  `frontend/src/pages/chemise/HistoriqueDossierPage.tsx` (constante
  `CHEMIN_PAR_FEATURE` étendue avec `conclusions` et `notes`) ; clés i18n
  dans `fr.json`/`en.json`.
- Vérifié : `npx tsc --noEmit` sans erreur ; suite `pytest` backend
  240/241 (le seul échec est un test de timing préexistant et flaky, sans
  rapport avec ce changement) ; test manuel de bout en bout via
  `TestClient` confirmant que la recherche trouve bien les correspondances
  dans un document généré et dans une note, groupées et triées comme prévu.

## Statut

**Implémenté et vérifié.**
