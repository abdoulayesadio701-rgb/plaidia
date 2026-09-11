# Optimisation des coûts API Anthropic - état des lieux

> Rapport uniquement -- aucun appel, aucun modèle et aucun prompt n'a été
> modifié pour le produire. Chiffres et lignes de code vérifiés dans le
> dépôt à la date de ce rapport (branche `main`).

## Résumé exécutif

- **32 appels** à l'API Anthropic au total dans le backend : 31 dans
  `analyse.py` (racine, importé par `backend/app/`) + 1 dans `extract.py`
  (transcription d'image). Aucun appel Anthropic direct dans
  `backend/app/quality_pipeline.py` ni `security_guard.py` -- ces deux
  modules orchestrent les fonctions de `analyse.py`, ils ne parlent jamais
  au réseau eux-mêmes.
- Aujourd'hui : **27 appels sur Sonnet** (`MODEL_ACTIF`), **5 sur Haiku**
  (`MODEL_LEGER`, déjà en place depuis le chantier "temps de traitement").
- **Précédent important à connaître avant toute reclassification** (voir
  §2.0) : un passage plus large à Haiku a déjà été essayé sur ce projet et
  **annulé** suite à un retour utilisateur sur la perte de profondeur des
  réponses. Ce rapport en tient compte et propose un périmètre Haiku
  volontairement plus étroit que ne le suggère la répartition brute
  "extraction/résumé -> Haiku" des consignes, avec un palier intermédiaire
  "à piloter" pour les cas ambigus plutôt qu'un basculement en bloc.
- **Aucune donnée de volume réel** (nombre d'appels/mois, tokens
  consommés par fonction) n'existe encore côté serveur -- la trace de
  latence ajoutée par le chantier perf (`EtapeTrace`) mesure des durées,
  pas des tokens. Toute estimation chiffrée ci-dessous est donc un ordre
  de grandeur basé sur la structure du code, pas une mesure -- voir §5.
- Aucune boucle de traitement de masse n'appelle Claude aujourd'hui (voir
  §3) : la Batch API n'a pas de cible de conversion immédiate dans ce
  dépôt, seulement des candidats futurs si l'app évolue vers de l'import
  ou de l'indexation en lot.
- Le contenu système est très largement statique et donc éligible au
  prompt caching quasiment sans changement de logique métier (voir §4) --
  c'est le levier au meilleur rapport gain/risque de ce rapport.

---

## 1. Inventaire complet des appels Anthropic

### 1.1 `analyse.py` (racine -- importé tel quel par le backend)

Modèles actuels : `MODEL_ACTIF = "claude-sonnet-4-6"` (analyse.py:97),
`MODEL_LEGER = "claude-haiku-4-5-20251001"` (analyse.py:109).

| Fonction | Ligne | Modèle | `max_tokens` | Tâche |
|---|---|---|---|---|
| `repondre_conversation` | 223 | Sonnet | 2800 | Réponse juridique en conversation multi-tours |
| `repondre_conversation_stream` | 246 | Sonnet | 2800 | Idem, en streaming |
| `simuler_objections` | 323 | Sonnet | 3800 | Génération d'objections probables du juge/adverse |
| `construire_chronologie` | 399 | Sonnet | 1800 | Structuration de dates/faits déjà fournis |
| `extraire_elements_cles` | 437 | Sonnet | 1500 | Extraction de dates/noms/références dans un document |
| `classifier_document` | 474 | Sonnet | 500 | Classification de la nature d'un document |
| `rediger_pv` | 527 | Sonnet | 2000 | Rédaction d'un PV d'audience à partir de notes |
| `analyser_requisitoire` | 561 | Sonnet | 1800 | Structuration du contenu d'un réquisitoire |
| `analyser_rapport_instruction` | 605 | Sonnet | 1800 | Structuration d'un rapport d'instruction |
| `rediger_note_client` | 627 | Sonnet | 1500 | Note explicative pour un client sans formation juridique |
| `resumer_dossier` | 640 | Sonnet | 2200 | Résumé d'un dossier accumulé sur plusieurs documents |
| `generer_plan_plaidoirie` | 664 | Sonnet | 3200 | Génération d'un plan de plaidoirie orale |
| `analyser_conclusions` | 692 | Sonnet | 3200 | Analyse d'arguments juridiques adverses + base de réfutation |
| `_verifier_coherence_globale_moyens` | 799 | **Haiku** | 200 | Détection de contradiction entre moyens déjà analysés séparément |
| `reviser_texte` | 860 | Sonnet | 2000 | Révision d'un texte selon instruction libre |
| `traduire_texte` | 904 | Sonnet | 4000 | Traduction juridique FR<->EN |
| `traiter_message_edition` | 958 | Sonnet | 3000 | Interprétation d'une demande d'édition en langage naturel |
| `verifier_procedure` | 1026 | Sonnet | 1800 | Détection d'anomalie procédurale |
| `controler_coherence` | 1076 | Sonnet | 1800 | Détection de contradictions factuelles entre documents |
| `consulter_position_jurisprudence` | 1147 | Sonnet | 1800 | Synthèse de la position jurisprudentielle sur un sujet |
| `identifier_notions_juridiques` | 1183 | **Haiku** | 400 | Préparation de recherche (pas de réponse juridique) |
| `consulter_jurisprudence` | 1254 | Sonnet | 2200 | Réponse sur ce que disent des sources juridiques |
| `traiter_notes` | 1304 | Sonnet | 1500 | Organisation de notes de travail informelles |
| `interpreter_intention` | 1356 | **Haiku** | 300 | Routage d'une commande en langage naturel |
| `analyser_style_adverse` | 1405 | Sonnet | 2500 | Analyse rhétorique/stylistique de conclusions adverses |
| `evaluer_garde_fou_entree` | 1471 | **Haiku** | 300 | Garde-fou sécurité d'entrée |
| `analyser_intention_juridique` | 1535 | **Haiku** | 500 | Routage d'intention dans le chat général |
| `verifier_juridiquement` | 1590 | Sonnet | 1500 | Agent vérificateur (cohérence citation/affirmation) |
| `critiquer_reponse` | 1652 | Sonnet | 1500 | Agent critique contradictoire |
| `valider_finalement` | 1696 | Sonnet | 1200 | Consolidation vérificateur + critique |
| `generer_strategie_combative` | 1761 | Sonnet | 3200 | Génération de stratégie combative (angles d'attaque) |

`analyser_conclusions_par_moyens` (827) n'appelle pas l'API elle-même :
elle découpe le texte en moyens puis appelle `analyser_conclusions` une
fois par moyen, en parallèle (chantier perf) -- comptée ci-dessus, pas en
double.

### 1.2 `extract.py`

| Fonction | Ligne | Modèle | `max_tokens` | Tâche |
|---|---|---|---|---|
| `_extract_image` | 129 | Sonnet (`"claude-sonnet-4-6"` en dur, pas la constante `MODEL_ACTIF`) | 2000 | Transcription OCR d'une image (vision) |

À noter : ce site n'utilise même pas `MODEL_ACTIF` -- le modèle y est
codé en dur, séparément. Une reclassification devra le traiter à part.

### 1.3 Orchestration (`backend/app/quality_pipeline.py`, `security_guard.py`)

Ces deux fichiers ne font **aucun appel réseau** -- ils appellent les
fonctions de `analyse.py` listées ci-dessus. Le point notable pour ce
rapport : `_executer_trio_qualite` (quality_pipeline.py:349) construit un
`contexte_sources` commun (jusqu'à 8000 caractères de sources + la
constante `REGLE_POSTURE_STRATEGIQUE`, quality_pipeline.py:43) et
l'envoie à **`verifier_juridiquement` et `critiquer_reponse` en
parallèle**, sur le même dossier -- c'est le principal point de contexte
répété entre appels d'une même requête (voir §4.2).

---

## 2. Répartition modèle proposée

### 2.0 Précédent à respecter (analyse.py:93-97)

```python
# Modèle utilisé pour toutes les analyses — centralisé ici pour pouvoir
# basculer facilement entre rapidité (Haiku) et profondeur (Sonnet).
# Retour à Sonnet suite au retour utilisateur : les réponses manquaient
# de profondeur avec Haiku — la qualité prime sur la vitesse pour cet usage.
MODEL_ACTIF = "claude-sonnet-4-6"
```

Et le commentaire du chantier "temps de traitement" juste après (99-108)
est explicite : Haiku est réservé "jamais à une fonction qui produit du
contenu juridique destiné à l'utilisateur final". C'est une règle plus
stricte que la consigne "extraction/résumé -> Haiku" de ce chantier --
`resumer_dossier`, `rediger_pv`, `rediger_note_client`,
`construire_chronologie` etc. sont des tâches de résumé/structuration au
sens strict, mais leur **sortie est un texte lu directement par
l'avocat, parfois transmis au client ou versé au dossier**. C'est
vraisemblablement le type de contenu visé par le retour utilisateur qui a
motivé le retour à Sonnet. Ce rapport propose donc un périmètre Haiku
plus étroit, avec un palier intermédiaire pour ne pas répéter cet échec.

### 2.1 Bucket A -- Haiku 4.5 (risque faible, sortie structurée ou mécanique)

Sortie non rédactionnelle (JSON structuré consommé par le front, pas de
prose lue telle quelle) ou tâche purement mécanique (transcription
fidèle). Aucun de ces appels ne produit le texte final vu par
l'utilisateur sans repasser par une étape humaine ou un autre agent.

| Fonction | Pourquoi Haiku convient |
|---|---|
| `extraire_elements_cles` | Retourne une liste structurée (dates, noms, références) -- pas de prose interprétative |
| `classifier_document` | Retourne une étiquette de classification -- `max_tokens=500`, tâche fermée |
| `extract.py::_extract_image` | Transcription fidèle d'image en texte -- pas de génération, à condition de vérifier que Haiku 4.5 dispose bien de la vision (à confirmer avant de basculer, voir §6) |

### 2.2 Bucket B -- Sonnet 5 (conservé)

Raisonnement juridique explicite, génération de plaidoirie, ou -- suite
au précédent de §2.0 -- contenu final rédigé destiné à être lu tel quel
par l'avocat ou son client.

| Fonction | Raison |
|---|---|
| `repondre_conversation` / `_stream` | Réponse juridique substantielle en conversation |
| `simuler_objections` | Anticipation stratégique |
| `generer_plan_plaidoirie` | Génération de plaidoirie (périmètre Sonnet explicite de la consigne) |
| `analyser_conclusions` | Cœur du raisonnement d'analyse d'arguments adverses |
| `verifier_procedure` | Détection d'anomalie procédurale -- enjeu réel si manquée |
| `consulter_position_jurisprudence` / `consulter_jurisprudence` | Interprétation de sources juridiques |
| `analyser_style_adverse` | Nourrit directement la stratégie d'audience |
| `verifier_juridiquement` / `critiquer_reponse` / `valider_finalement` / `generer_strategie_combative` | Trio qualité + stratégie -- garde-fous de fond, pas de marge d'erreur acceptée |
| `rediger_note_client` | Lu directement par un client sans formation juridique -- la barre de qualité rédactionnelle est la plus haute de tout le périmètre |
| `construire_chronologie`, `rediger_pv`, `analyser_requisitoire`, `analyser_rapport_instruction`, `resumer_dossier`, `traiter_notes` | Résumé/structuration au sens de la consigne, mais sortie = document de travail juridique lu tel quel (voir §2.0) |
| `traiter_message_edition` | Répond en direct à l'utilisateur sur son propre dossier -- qualité perçue immédiate |

### 2.3 Bucket C -- à piloter avant de trancher

Tâches de transformation (traduction, révision, comparaison) qui
ressemblent à des candidats Haiku sur le papier, mais dont la sortie est
soit lue telle quelle, soit sensible à la nuance juridique. Le risque
d'y répéter l'épisode de §2.0 est réel : recommandation = ne rien
basculer avant un test A/B mesuré (voir §6), pas une bascule silencieuse.

| Fonction | Tension |
|---|---|
| `reviser_texte` | Portée très variable selon l'instruction libre : simple correction (Haiku suffirait) vs renforcement argumentatif (Sonnet nécessaire) -- pas de moyen de distinguer les deux sans classification préalable |
| `traduire_texte` | Traduction = transformation plutôt que génération, bon candidat en théorie, mais la précision terminologique juridique FR/EN a un coût d'erreur élevé |
| `controler_coherence` | Comparaison multi-documents -- pattern-matching en apparence, mais la subtilité des contradictions factuelles varie beaucoup |

---

## 3. Traitements de masse -> Batch API

**Constat : aucune boucle de traitement en masse n'appelle Claude
aujourd'hui dans ce dépôt.**

- `judilibre.py::collecter_jurisprudence` (et la route
  `POST /api/jurisprudence/collecter`) ne fait **aucun appel Anthropic** :
  c'est un appel REST direct à l'API Judilibre, suivi de formatage Python
  pur (`_extract_summary`, `_format_reference`). Il n'y a donc pas
  d'"indexation de jurisprudence par LLM" à convertir en Batch API pour
  l'instant.
- `POST /api/dossiers/{id}/documents` (`importer_document`,
  routers/dossiers.py:115) traite **un seul fichier à la fois** -- pas de
  boucle multi-documents qui appellerait `classifier_document` ou
  `extraire_elements_cles` en série sur un lot.

Il n'y a donc pas de conversion à proposer aujourd'hui sans construire
d'abord la fonctionnalité de traitement en lot elle-même. Deux candidats
si ce type de fonctionnalité apparaît plus tard :

- **Import multi-documents** : si un import de dossier en lot (plusieurs
  fichiers d'un coup) est ajouté, `classifier_document` +
  `extraire_elements_cles` sur chaque fichier seraient un candidat
  naturel à la Batch API (non-urgent du point de vue utilisateur -- le
  classement peut arriver a posteriori, pas en bloquant l'upload).
- **Ré-indexation en lot d'un corpus de jurisprudence déjà collecté** (si
  un enrichissement par LLM -- résumé, tags -- était ajouté au corpus
  validé de `backend/app/routers/jurisprudence.py`), plutôt qu'un appel
  synchrone par décision.

Aucune action de code n'est donc recommandée sur ce point pour l'instant.

---

## 4. Prompt caching

C'est le levier le plus immédiatement actionnable : gain de coût sans
aucun changement de logique métier, juste une restructuration de la
manière dont le contenu est découpé dans l'appel.

### 4.1 Système -- contenu 100% statique, jamais modifié par requête

Les 29 constantes `*_SYSTEM_PROMPT` de `analyse.py` (711 à 7665 caractères
selon la fonction, ex. `QUESTION_SYSTEM_PROMPT` 7665 caractères ≈ 1900
tokens, `EDITION_SYSTEM_PROMPT` 6253 ≈ 1550 tokens,
`GARDE_FOU_SYSTEM_PROMPT` 3507, `JURISPRUDENCE_CONSULT_SYSTEM_PROMPT`
4053) sont des chaînes Python figées, identiques à chaque appel, pour
tous les utilisateurs. C'est exactement le cas d'usage visé par le
prompt caching Anthropic (`cache_control: {"type": "ephemeral"}` sur un
bloc de `system`).

Aujourd'hui, `system` est construit comme une simple chaîne concaténée :

```python
system = QUESTION_SYSTEM_PROMPT + _directive_langue()
if contexte_recherche:
    system += contexte_recherche
```

(`repondre_conversation`, analyse.py:232-234 -- même schéma dans la
majorité des fonctions). La partie stable (`QUESTION_SYSTEM_PROMPT`) et
la partie variable (`_directive_langue()`, `contexte_recherche`) sont
déjà deux morceaux distincts avant d'être concaténés -- la structure
actuelle se prête donc bien à un découpage en liste de blocs sans
réécrire les prompts eux-mêmes :

```python
system=[
    {"type": "text", "text": QUESTION_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": _directive_langue() + (contexte_recherche or "")},
]
```

`_directive_langue()` ne varie qu'entre FR/EN (2 valeurs possibles) --
elle pourrait même être découpée en un second petit bloc cacheable par
langue si le volume le justifie, mais l'essentiel du gain vient du
premier bloc.

**Seuil à vérifier avant de généraliser** : le cache Anthropic n'active
un breakpoint qu'au-delà d'un minimum de tokens (de l'ordre de 1024 pour
les modèles Sonnet, 2048 pour Haiku, à confirmer sur la doc tarifaire au
moment de l'implémentation). Les prompts système les plus courts de ce
projet (`COHERENCE_MOYENS_SYSTEM_PROMPT`, 846 caractères ≈ 210 tokens,
`CLASSEMENT_SYSTEM_PROMPT`, 887 caractères ≈ 220 tokens) sont probablement
sous ce seuil et ne bénéficieraient d'aucun cache -- inutile d'y ajouter
la complexité. Les prompts au-dessus de ~1500-2000 caractères sont les
candidats sérieux (une bonne moitié de la liste du §1.1).

### 4.2 Contexte dossier/jurisprudence -- répété entre agents d'une même requête

Dans `_executer_trio_qualite` (quality_pipeline.py:349-375), le même
`contexte_sources` (jusqu'à 8000 caractères de sources + la règle
`REGLE_POSTURE_STRATEGIQUE`) part vers `verifier_juridiquement` **et**
`critiquer_reponse` en parallèle pour la même requête -- actuellement ce
bloc est injecté dans le **message utilisateur** (pas dans `system`),
via une simple f-string :

```python
contenu += f"\n\nSources disponibles pour juger la cohérence :\n{contexte_sources}"
```

(`verifier_juridiquement`, analyse.py:1605). Le cache Anthropic
fonctionne aussi sur des blocs de `messages` (pas seulement `system`) --
mais deux appels **strictement parallèles** avec un cache encore vide au
moment du second n'obtiennent aucun hit entre eux (le premier n'a pas eu
le temps d'écrire le cache). Le vrai gain ici n'est pas intra-requête,
mais **inter-requêtes sur un même dossier** : un avocat qui enchaîne
résumé, puis plan de plaidoirie, puis analyse de conclusions sur le même
dossier dans la même session réutilise le même `contexte_dossier` /
`contexte_recherche` à chaque appel. Marquer ce bloc en cache (avec le
contenu variable placé strictement après, jamais avant, dans la
structure du message) permettrait des hits sur ces enchaînements
naturels -- à condition de garder une clé de cache stable (même texte de
dossier octet pour octet) entre deux appels successifs sur ce dossier.

### 4.3 Ce que ce rapport ne préconise pas encore

Restructurer `system` en liste de blocs sur les ~15-20 fonctions
concernées touche à un appel qui fonctionne aujourd'hui dans 31+ endroits
-- ce n'est pas un changement à faire d'un coup. Recommandation pour la
suite (si validée) : commencer par les 2-3 prompts les plus volumineux
et les plus appelés (`QUESTION_SYSTEM_PROMPT` via
`repondre_conversation`/`_stream`, `EDITION_SYSTEM_PROMPT`, le trio
qualité), mesurer le taux de cache hit réel (`response.usage` renvoie
`cache_creation_input_tokens`/`cache_read_input_tokens`), puis étendre.

---

## 5. Estimation d'impact

Sans données de volume réel par fonction, une estimation en euros/mois
ne serait pas fiable -- ce serait inventer un chiffre. Ordre de grandeur
qualitatif à la place :

- **Répartition modèle (§2)** : sur 27 appels actuellement sur Sonnet,
  3 basculeraient immédiatement en bucket A, ~4 de plus si le pilote du
  bucket C valide la qualité -- entre 10% et 25% du volume d'appels
  "lourds" suivant l'issue du pilote. Haiku étant généralement plusieurs
  fois moins cher par token que Sonnet (le ratio exact dépend de la
  tarification en vigueur au moment de la bascule -- à vérifier sur
  `anthropic.com/pricing` plutôt que de se fier à un chiffre de ce
  rapport), l'effet sur la facture de ces fonctions-là serait net même
  sur un périmètre restreint.
- **Batch API (§3)** : impact nul aujourd'hui, faute de traitement de
  masse existant.
- **Prompt caching (§4)** : c'est le levier qui touche le plus large
  volume sans aucun risque de qualité (le modèle voit exactement le même
  texte, seule la facturation change) -- potentiellement le gain net le
  plus significatif du lot, en particulier sur les fonctions à fort trafic
  et gros prompt système (`repondre_conversation`/`_stream`, chat général).

**Recommandation avant tout chiffrage plus précis** : instrumenter
`response.usage.input_tokens` / `output_tokens` (et
`cache_read_input_tokens` une fois le caching en place) dans le
`EtapeTrace` existant du chantier perf -- ça donnerait en quelques jours
d'usage réel des chiffres bien plus solides que n'importe quelle
estimation a priori.

---

## 6. Prochaines étapes (si tu valides une partie de ce rapport)

Aucune de ces actions n'a été faite -- ce rapport s'arrête à
l'inventaire et aux propositions, comme demandé.

1. Vérifier que Haiku 4.5 supporte la vision avant de toucher à
   `extract.py::_extract_image` (bucket A).
2. Basculer le bucket A (3 fonctions) sur `MODEL_LEGER`/Haiku, en gardant
   `MODEL_ACTIF`/Sonnet pour tout le reste -- changement isolé et à
   faible risque.
3. Ajouter le comptage de tokens (`response.usage`) à `EtapeTrace` pour
   obtenir de vraies données de volume avant d'aller plus loin sur le
   bucket C.
4. Piloter le bucket C fonction par fonction (pas en bloc), avec
   comparaison qualitative des sorties Haiku vs Sonnet sur des cas réels
   -- exactement la méthode qui aurait évité le retour en arrière déjà
   documenté en §2.0.
5. Prototyper le prompt caching sur 2-3 prompts système parmi les plus
   gros/plus appelés (§4.3), mesurer le taux de hit réel avant de
   généraliser.
