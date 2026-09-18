# Idée — Mode Entraînement chronométré à la plaidoirie (espace Avocat)

Date : 2026-09-18

## Constat

L'espace Avocat génère déjà un **Plan de plaidoirie** structuré en sections et
un **Simulateur d'objections** pour s'entraîner à répondre à la partie
adverse. Mais rien n'aide l'avocat à répéter concrètement son oral avant
l'audience, alors que le temps de parole est souvent limité ou contraint
(délais imposés par le magistrat, tribunaux correctionnels chargés, etc.).
C'est un besoin réel et non couvert par l'existant.

## Fonctionnalité proposée : « Mode Entraînement »

Nouvelle page dans l'espace Avocat (Arsenal), accessible depuis un plan de
plaidoirie déjà généré : `POST /arsenal/plan/{document_id}/entrainement` (ou
directement depuis `PlanPlaidoiriePage.tsx`, bouton « 🎙 S'entraîner »).

### Fonctionnement

1. **Répartition du temps** : l'utilisateur indique un temps total imparti
   (ex. 15 min). L'IA répartit ce temps entre les sections du plan déjà
   généré, proportionnellement à leur longueur/importance (réutilise le texte
   du plan existant, pas de nouvelle génération de contenu juridique).
2. **Répétition chronométrée** : un chronomètre par section démarre quand
   l'avocat clique « Je commence cette section ». Alerte visuelle (couleur qui
   change) quand le temps alloué à la section est dépassé — comme la
   `JaugeConfiance` existante mais appliquée au temps.
3. **Bilan de fin de répétition** : tableau récapitulatif (section / temps
   alloué / temps réel / écart), avec une synthèse texte généré par l'IA
   ("Vous avez dépassé le temps sur l'exposé des faits de 3 minutes,
   envisagez de le raccourcir de X phrases ; l'argumentation principale est
   dans les temps").
4. **Persistance** : comme les autres résultats Arsenal, le bilan est
   sauvegardé en base (`documents_generes`, feature="entrainement_plaidoirie")
   et réapparaît si on revient sur le dossier (réutilise
   `useDernierDocumentGenere`, pattern déjà en place).
5. **Export** : bilan exportable en Word via `exporter_texte_libre_word`
   (pattern déjà utilisé pour PV d'audience, cohérence, etc.) — utile pour
   garder une trace de sa progression d'une répétition à l'autre.

### Pourquoi c'est cohérent avec l'existant

- Ne génère aucun nouveau contenu juridique par IA à partir de zéro : elle
  réutilise le plan déjà produit, donc risque d'hallucination minimal.
- Réutilise 100% des patterns déjà en place dans le projet : persistance
  (`useDernierDocumentGenere`), export Word (`exporter_texte_libre_word`),
  jauge visuelle (`JaugeConfiance`), suppression avec confirmation
  (`ConfirmerModal`).
- Différenciant réel : aucun des outils actuels de Plaid'IA n'aide à la
  **prestation orale** elle-même, seulement à la préparation écrite.

### Effort estimé

Petit à moyen : 1 endpoint backend (répartition du temps + synthèse du bilan,
logique simple sans nouvel appel modèle coûteux si on se limite à une
répartition proportionnelle à la longueur du texte), 1 page frontend avec
logique de chronomètre côté client (pas de streaming nécessaire), export
réutilisant le pattern existant.

## Statut

Idée proposée, non implémentée. À valider avec l'utilisateur avant tout
développement.
