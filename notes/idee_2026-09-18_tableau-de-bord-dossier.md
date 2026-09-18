# Idée — Tableau de bord du dossier actif (page d'accueil)

Date : 2026-09-18
Espaces concernés : **Avocat et Greffier** (page d'accueil commune)
Statut : **✅ implémentée et testée — 2026-09-18**

## Constat

`HomePage.tsx` n'affiche, quand un dossier est sélectionné, que son nom, son
domaine et une phrase générique. Or le dossier accumule maintenant des données
utiles qu'il faut aller chercher page par page : échéances de procédure,
bordereau de pièces, dernier plan, dernière analyse, dernier entraînement,
notes. Rien ne répond d'un coup d'œil à « où en est ce dossier, et qu'est-ce
qui est urgent ? ».

## Fonctionnalité proposée : « Tableau de bord du dossier »

Sur la page d'accueil, sous le nom du dossier, quelques cartes cliquables :

1. **Prochaine échéance** : le délai de procédure non dépassé le plus proche
   (badge d'urgence, jours restants), ou « échéance dépassée » en rouge s'il y
   en a une ; lien vers « Suivi des délais ».
2. **Pièces** : nombre de pièces au bordereau ; lien vers « Bordereau de pièces ».
3. **Documents générés** : les 5 plus récents (plan, analyse, résumé,
   chronologie...) avec leur statut, liens directs (via `CHEMIN_PAR_FEATURE`).
4. **Dernier entraînement** : total alloué / réel et écart, lien vers la page.
5. **Alertes d'articles modifiés** : le compteur déjà calculé pour la fiche
   dossier (`useAlertesArticlesDossier`), réutilisé tel quel.

## Choix par défaut proposés (à valider)

- **Sans IA et sans nouvel endpoint** : `GET /api/dossiers/{id}/documents-generes`
  renvoie déjà tous les documents avec leur contenu (délais, bordereau,
  entraînement compris) ; l'agrégation se fait côté navigateur.
- **Une carte n'apparaît que si elle a une donnée** : pas de cartes vides
  qui encombrent un dossier neuf ; à la place, un rappel des premières actions
  possibles.
- **Aucune modification de l'accueil sans dossier** (invitation actuelle conservée).
- **Portée V1** : pas de graphiques, pas d'historique d'activité, pas de
  personnalisation des cartes.

## Effort estimé

Petit : 1 composant + adaptation de `HomePage.tsx`, réutilise
`listerDocumentsGeneres`, `CHEMIN_PAR_FEATURE` et les classes d'urgence déjà
utilisées par le suivi des délais. Tests : logique d'agrégation extraite en
fonction pure (choix de la prochaine échéance, tri, comptage) puis vérification
navigateur.

## Pourquoi maintenant

Les trois dernières fonctionnalités (délais, entraînement, bordereau) ont créé
des données qui n'ont aucun point de synthèse ; le tableau de bord les rend
visibles sans rien ajouter à stocker.

## Implémentation (2026-09-18)

Validée puis implémentée comme proposé : frontend uniquement, sans IA et sans
nouvel endpoint.

- **Agrégation pure** `components/tableauDeBord/synthese.ts` (`synthetiser`) :
  prochaine échéance = la plus proche non dépassée du **dernier** calcul de
  délais, échéances dépassées comptées à part, nombre de pièces du dernier
  bordereau, dernier entraînement, 5 documents récents (hors délais /
  bordereau / entraînement, qui ont leur carte). Tolère un contenu inattendu.
- **Composant** `TableauDeBord.tsx`, affiché par `HomePage.tsx` sous le nom du
  dossier : cartes cliquables (échéance -> délais, pièces -> bordereau,
  entraînement, veille -> historique, récents -> leur page). Une carte n'apparaît
  que si elle a une donnée ; sinon un message d'aide.
- **Refactor pour éviter la duplication** : `config/echeances.ts` (dates et
  urgence, repris de DelaisPage), `config/durees.ts` (repris de
  EntrainementPage), `config/cheminsDocuments.ts` (`CHEMIN_PAR_FEATURE`,
  extrait de HistoriqueDossierPage).
- **Non fait** : graphiques, historique d'activité, personnalisation.

Vérifié : `tsc --noEmit` propre ; `vitest` 42/42 (9 nouveaux tests sur
l'agrégation : échéances passées / du jour / dernier calcul seul, pièces,
entraînement, récents, contenu inattendu) ; scénario réel dans Chromium
(instances isolées) : cartes échéance (17 jours, prorogée au lundi 5 octobre),
pièces, entraînement, récents, lien vers le bordereau, dossier vide ; aucune
erreur JS.

## Statut

**✅ Implémentée et testée — 2026-09-18.**
