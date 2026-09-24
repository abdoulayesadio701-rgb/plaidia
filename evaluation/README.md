# Évaluation anti-hallucination de Plaid'IA

Ce dossier mesure ce que Plaid'IA promet : ne pas inventer de sources juridiques, signaler ce qu'il ne peut pas confirmer, et ne pas refuser à tort les demandes normales d'un avocat. Il rejoue le **vrai chemin du chat de production** (mêmes prompts, mêmes modèles, mêmes agents), pas une copie.

## Ce qui est mesuré

| # | Mesure | Comment |
|---|---|---|
| 1 | **Faux refus du garde-fou** : demandes légitimes refusées à tort | 25 demandes réelles d'avocats (impératives, longues, courtes, OHADA...), chacune répétée 3 fois car le modèle n'est pas déterministe |
| 1 | **Détection du garde-fou** : attaques bloquées | 11 attaques (injection de prompt, jailbreak, contenu illicite, hors sujet, consigne cachée dans un document) |
| 1 | **Avant / après** | Le même jeu est rejoué avec le prompt du garde-fou d'avant la correction (`--garde-fou-ancien`) |
| 2 | **Exactitude des citations d'articles** | 20 questions de droit français, chaque article balisé `[ART:n:CODE]` est comparé à une liste d'articles attendus et d'articles réels connus |
| 3 | **Résistance aux pièges** | 13 questions portant sur des sources qui n'existent pas (article inexistant, mauvais code, arrêt fictif, loi fictive) : le modèle l'adopte-t-il, ou signale-t-il qu'elle n'existe pas ? |
| 4 | **Rattrapage par le vérificateur** | Sur les fictifs adoptés : le vérificateur les signale-t-il, les valide-t-il à tort, ou les ignore-t-il ? Et combien de vrais articles marque-t-il à tort NON_VERIFIE ? |

Tous les résultats sont donnés avec leur **intervalle de confiance à 95 %** (méthode de Wilson), parce que les échantillons sont petits : 2 refus sur 25 n'a pas la même valeur que 20 sur 250.

## Lancer

Depuis la racine du dépôt :

```bash
python -m evaluation.run_evaluation --estimer                        # coût prévu, aucun appel
python -m evaluation.run_evaluation --dry-run                        # toute la chaîne avec un faux modèle, gratuit
python -m evaluation.run_evaluation --garde-fou-ancien               # vrai run (clé apikey.txt), avec l'avant/après
python -m evaluation.run_evaluation --reprendre <run_id>             # reprend un run interrompu
python -m evaluation.run_evaluation --rapport <run_id>               # régénère le rapport après revue manuelle
```

- **Coût** : de l'ordre de 2 à 3 $ pour un run complet (Sonnet pour la réponse, le vérificateur et le critique ; Haiku pour le garde-fou et l'agent de compréhension). `--estimer` donne le chiffre exact pour vos réglages. Un plafond `--budget-usd` (6 $ par défaut) arrête proprement le run.
- **Durée** : une dizaine de minutes.
- Résultats dans `evaluation/resultats/<run_id>/` : `brut.jsonl` (toutes les réponses), `meta.json` (commit, modèles, coût), `agrege.json`, `RESULTATS.md`.
- Les tarifs de `run_evaluation.py` sont des valeurs publiques à vérifier avant de citer un coût.

## Revue manuelle (étape obligatoire)

Une liste d'articles ne sera jamais exhaustive. Les citations qui ne sont ni attendues ni connues comme réelles sont classées **« à revoir »** : elles ne sont **jamais comptées comme exactes** tant qu'un humain ne les a pas tranchées. Après un run :

1. Ouvrir `RESULTATS.md` : la liste des citations à revoir y figure.
2. Vérifier chacune sur Légifrance.
3. Reporter le verdict dans `evaluation/revue_manuelle.json` :
   - `"articles"` : `{"CCIV:1240-9": "inventee"}` (valeurs : `reelle`, `inventee`, `mal_attribuee`)
   - `"pieges"` : `{"P03": "signale_inexistant"}` pour corriger le classement automatique d'une question-piège après lecture de la réponse (valeurs : `adopte`, `signale_inexistant`, `non_cite`)
4. Relancer `--rapport <run_id>`. Les corrections faites à la main sont mentionnées dans le rapport.

## Limites, à citer avec les chiffres

- **Petit échantillon** : 20 questions de fond, 13 pièges, 36 demandes pour le garde-fou. Les intervalles de confiance sont larges, c'est voulu, ils sont affichés.
- **Une seule réponse par question de fond et par piège** : le modèle varie d'une génération à l'autre. Seul le garde-fou est répété (3 fois).
- **Référentiel écrit à la main** par l'auteur du projet, d'où la revue manuelle des citations non listées. Il ne remplace pas une vérification par un juriste.
- **Jurisprudence non vérifiée automatiquement** : les références `[JURISPRUDENCE:...]` sont comptées mais pas contrôlées (il faudrait interroger Judilibre). Les pièges de jurisprudence, eux, sont mesurés.
- **Le chat de production n'a pas de corpus de sources** (sauf recherche live activée) : le contrôle déterministe des citations vaut alors `AUCUNE_SOURCE` et le statut repose sur le seul modèle vérificateur. Le run mesure ce comportement réel, pas celui des fonctions d'analyse avec corpus.
- **Détection des fictifs adoptés** : automatique par balise, numéro et formules de déni ("n'existe pas"...), donc imparfaite. D'où la correction manuelle possible, tracée dans le rapport.
- **Ce n'est pas une évaluation de la qualité juridique du raisonnement**, seulement de la fiabilité des sources citées et du comportement du garde-fou.

## Fichiers

| Fichier | Rôle |
|---|---|
| `jeu_evaluation.json` | Les questions, les articles attendus, les fictifs |
| `metriques.py` | Calcul des métriques (fonctions pures, testées) |
| `run_evaluation.py` | Lancement, plafond de dépense, reprise, rapport |
| `revue_manuelle.json` | Verdicts humains (à remplir après un run) |
| `resultats/` | Un dossier par run |
| `../backend/tests/test_evaluation.py` | Tests de tout ce qui précède, sans aucun appel réseau (tournent en CI) |
