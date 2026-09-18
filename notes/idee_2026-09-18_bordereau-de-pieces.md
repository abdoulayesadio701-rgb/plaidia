# Idée — Bordereau de pièces du dossier

Date : 2026-09-18
Espaces concernés : **Avocat et Greffier** (fonctionnalité partagée)
Statut : **✅ implémentée et testée — 2026-09-18**

## Constat

Le texte des documents importés est ajouté aux faits du dossier
(`db.ajouter_aux_faits`, avec le nom du fichier comme source), mais l'application
ne garde aucune **liste structurée des pièces** : ni numéro, ni intitulé, ni date,
ni partie qui la produit. Or, en procédure, l'avocat joint à ses conclusions un
bordereau de pièces numérotées, et le greffier vérifie et tient cette liste. Les
deux le refont aujourd'hui à la main, hors de l'outil.

## Fonctionnalité proposée : « Bordereau de pièces »

Une page par dossier (`requiresDossier: true`), utilisable dans les deux espaces :

1. **Saisie** : ajouter une pièce (numéro proposé automatiquement, intitulé,
   date du document, partie qui la produit, observation libre), modifier,
   supprimer, réordonner.
2. **Reprise depuis l'import** : bouton « Ajouter depuis un document importé »
   qui préremplit l'intitulé avec le nom du fichier (aucune analyse IA).
3. **Numérotation** : automatique et modifiable ; renumérotation en un clic
   après réorganisation.
4. **Export Word** : tableau « N° / Intitulé / Date / Produite par », prêt à
   annexer aux conclusions (`exporter_texte_libre_word`, comme les autres exports).
5. **Persistance** : rattachée au dossier, retrouvable via la recherche
   transversale et « Documents générés ».

## Choix par défaut proposés (à valider)

- **Sans IA** : une liste de pièces est une donnée de fait, pas un texte généré ;
  aucune clé API nécessaire, identique en mode démo.
- **Stockage** : une seule entrée `documents_generes` (feature="bordereau") mise à
  jour à chaque modification, plutôt que une nouvelle table. À trancher : la
  mise à jour d'un document existe-t-elle déjà côté `db.py` (à vérifier), sinon
  une table dédiée `pieces` est plus propre.
- **Périmètre V1** : pas de lien automatique entre une pièce et son fichier, pas
  d'OCR, pas de détection de pièces manquantes.

## Effort estimé

Moyen : 1 page (formulaire + tableau réordonnable), 3 endpoints (lire,
enregistrer, exporter), tests de numérotation et d'export.

## Pourquoi maintenant

Réutilise les briques déjà en place (persistance par dossier, export Word,
recherche transversale) et comble un manque concret qui touche les deux métiers.

## Implémentation (2026-09-18)

Validée puis implémentée comme proposé, sans IA :

- **Stockage tranché** : `db.mettre_a_jour_document_genere` existe, donc une
  seule entrée `documents_generes` (feature="bordereau") par dossier, mise à
  jour sur place (pas de nouvelle table). Retrouvable dans « Documents
  générés » et par la recherche transversale.
- **API** : `GET/PUT /api/bordereau/{dossier_id}`, `GET .../sources` (noms des
  documents déjà importés, lus dans les en-têtes posés par
  `db.ajouter_aux_faits`, textes collés exclus), `GET .../export`.
  Numéros uniques exigés (422 sinon), tri par numéro à l'enregistrement.
- **Export Word** : vrai tableau N° / Intitulé / Date / Produite par, sans page
  de garde (document à annexer) : `export.exporter_bordereau_word`.
- **Page partagée** `BordereauPage.tsx`, routes `/chemise/bordereau` (Avocat) et
  `/greffier/bordereau` (Greffier), mêmes données : ajout, réordonnancement
  (↑ ↓) et retrait avec renumérotation automatique, numéro modifiable à la main
  (enregistrement bloqué en cas de doublon), reprise depuis un document
  importé, export désactivé tant que des modifications ne sont pas
  enregistrées.
- **Non fait** : suppression du bordereau entier (on enregistre une liste
  vide), lien pièce <-> fichier, détection de pièces manquantes.
- Choix de V1 à valider : la date d'une pièce n'est pas déduite de la date
  d'import (saisie manuelle).

Fichiers : `backend/app/bordereau.py`, `backend/app/routers/bordereau.py`,
`backend/app/schemas/bordereau.py`, `backend/tests/test_bordereau.py`,
`frontend/src/pages/chemise/BordereauPage.tsx`, `frontend/src/api/bordereau.ts`
(nouveaux) ; `export.py`, `backend/app/main.py`, `frontend/src/api/{index,types}.ts`,
`frontend/src/router.tsx`, `frontend/src/config/navigation.ts`,
`frontend/src/pages/chemise/HistoriqueDossierPage.tsx`, `fr.json` / `en.json`.

Vérifié : `tsc --noEmit` propre ; `pytest` backend 278/278 (12 nouveaux tests,
dont lecture du tableau Word) ; scénario réel dans Chromium (instances
isolées) : saisie, réordonnancement, blocage des doublons, reprise depuis un
import, enregistrement, même bordereau côté Greffier, export Word relu,
présence dans « Documents générés » et la recherche, aucune erreur JS.

## Mise à jour (2026-09-18, suite)

- **Suppression du bordereau entier : faite** (bouton « Supprimer le bordereau »
  avec confirmation ; supprime l'entrée `documents_generes`).
- **Lien pièce <-> fichier : non faisable en l'état** : l'application ne conserve
  pas les fichiers importés, seulement leur texte extrait ajouté aux faits. Il
  faudrait d'abord stocker les fichiers (nouveau stockage, taille, sécurité) ;
  décision produit à prendre.
- Détection de pièces manquantes : toujours non faite.
