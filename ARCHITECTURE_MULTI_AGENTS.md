# Architecture multi-agents de vérification — Plaid'IA

Ce document décrit l'architecture de vérification en profondeur ajoutée à
Plaid'IA : l'agent qui rédige une analyse n'est plus le seul juge de sa
propre réponse. Complète (ne remplace pas) `ARCHITECTURE_CHAT_CONTEXTUEL.md`,
dont plusieurs mécanismes sont réutilisés tels quels (voir §0).

## 0. Ce qui existait déjà et a été réutilisé

- **`analyse.py`** (racine) : tous les prompts système + `_client()` +
  `MODEL_ACTIF`. Les 5 nouveaux agents suivent exactement la même convention
  que les ~20 fonctions déjà présentes (`XXX_SYSTEM_PROMPT` + fonction qui
  appelle `_client()`, parse le JSON, applique des `setdefault`).
- **`backend/app/chat_actions.py`** : le pattern « le modèle propose, le
  code dispose » (validation d'une action LLM par du code avant application)
  est le précédent architectural direct du vérificateur/validateur.
- **`recherche_juridique._appel_avec_timeout`** : idiome ThreadPoolExecutor +
  timeout strict, repris pour protéger chaque agent qualité.
- **`db.get_corpus_valide` / `db.get_jurisprudence_validee`** et les
  résultats de `recherche_juridique.rechercher_contexte_juridique` : seule
  vérité déterministe disponible pour vérifier une citation.
- **`demo.py`** : le pipeline est entièrement court-circuité en mode démo,
  comme le reste de l'application (réponses préenregistrées).

## 1. Architecture cible

```
Utilisateur
   → Garde-fou d'entrée              (SÉCURITÉ — app.security_guard)
   → [Agent de compréhension]        (Chat juridique uniquement — voir §3)
   → Agent principal                 (inchangé — analyse.py existant)
   → Vérificateur juridique          (QUALITÉ — app.quality_pipeline)
   → Agent critique / contradicteur  (QUALITÉ)
   → Agent de validation finale      (QUALITÉ)
   → Réponse utilisateur (+ bloc `verification` additif)
```

Séparation stricte sécurité / qualité dans le code : `security_guard.py` ne
contient aucune logique de vérification de contenu ; `quality_pipeline.py`
ne contient aucune décision d'autorisation/refus d'une demande.

## 2. Deux pipelines, pas un seul appliqué partout

Appliquer les 5 agents à toutes les fonctionnalités aurait été le piège
explicitement à éviter (agents ajoutés « pour la forme »). Classification :

- **Pipeline complet** (`executer_pipeline_complet`) — garde-fou → agent
  principal (inchangé) → vérificateur → critique → validation finale. Pas
  d'agent d'intention : la tâche est déjà connue par l'endpoint appelé.
  Appliqué à `POST /api/analyse/conclusions`, `/plan`, `/simulateur`,
  `POST /api/jurisprudence/consulter` — les 4 fonctionnalités qui produisent
  des affirmations juridiques sourcées à fort enjeu.
- **Pipeline conversationnel** (`executer_garde_fou_et_intention` +
  `executer_trio_qualite_si_necessaire`) — garde-fou → agent de
  compréhension → agent principal → trio qualité **seulement si**
  `intention.necessite_verification_approfondie` est vrai. Seul endroit où
  la tâche n'est pas connue à l'avance (`POST /api/chat/stream`), donc seul
  endroit où l'agent de compréhension a un rôle mesurable.
- **Garde-fou seul** — `POST /api/chat/contextuel` : une édition locale est
  déjà protégée par la validation de `chat_actions` (scope/opération
  vérifiés contre le résultat réel avant toute application) ; ajouter le
  trio qualité sur chaque petite modification serait disproportionné.
- **Aucun changement** — note client, PV d'audience, chronologie,
  extraction, classement, cohérence, vérification procédurale, style,
  traduction, notes, résumé de dossier : déjà cadrées par leurs prompts
  (« n'invente rien »), pas d'affirmations sourcées à contrôler.
- `POST /api/analyse/rapport-complet` reste volontairement **sans** le
  pipeline qualité (voir commentaire dans `routers/analyse.py`) : il génère
  déjà jusqu'à 2 analyses en parallèle, y ajouter le trio pour chacune
  multiplierait le nombre d'appels Claude d'une seule requête HTTP par ~4-5,
  au risque de délais inacceptables. Utiliser les endpoints `/plan` et
  `/simulateur` dédiés pour un contrôle complet.

## 3. Les 5 agents

| Agent | Fichier (prompt + appel) | Rôle mesurable |
|---|---|---|
| Garde-fou d'entrée | `analyse.evaluer_garde_fou_entree` | `{allowed, risk_level, reason, requires_clarification}` — permissif par défaut, ne bloque jamais sur sa propre erreur technique. |
| Compréhension / intention | `analyse.analyser_intention_juridique` | Classe une demande libre du Chat juridique et décide si le trio qualité est nécessaire — n'existe que là où la tâche n'est pas déjà connue. |
| Vérificateur juridique | `analyse.verifier_juridiquement` + `quality_pipeline._verifier_citations` (déterministe) | Statuts `VERIFIE / PARTIELLEMENT_VERIFIE / A_VERIFIER / NON_VERIFIE` par affirmation. Le contrôle déterministe (regex + comparaison aux sources fournies) **fait autorité en code** (`_appliquer_autorite_deterministe`) : une citation absente des sources reste `NON_VERIFIE` même si la couche LLM prétend le contraire. |
| Critique / contradicteur | `analyse.critiquer_reponse` | Cherche activement les faiblesses (raisonnement insuffisant, conclusion catégorique, argument adverse ignoré...), comme le ferait un avocat adverse — jamais une reformulation. |
| Validation finale | `analyse.valider_finalement` | Consolide vérificateur + critique en `{statut_global, points_a_verifier, points_forts, synthese_utilisateur}` — reçoit uniquement les deux verdicts précédents, jamais l'analyse originale : ne peut donc pas fabriquer de nouveau contenu juridique. |

## 4. Dégradation propre (jamais de fonctionnalité cassée)

Chaque agent qualité est encapsulé par `quality_pipeline._appel_protege`
(timeout strict de 20s, aucune exception ne remonte). En cas d'échec ou de
délai dépassé, le résultat de l'agent principal est renvoyé **inchangé**,
avec un bloc `verification` dégradé (basé sur le contrôle déterministe seul)
plutôt qu'absent ou qu'une erreur 500. Voir `backend/tests/test_quality_pipeline.py`.

## 5. Schéma de réponse (additif)

`ConclusionsOut`, `PlanOut`, `SimulateurOut`, `ConsulterOut` gagnent un champ
optionnel `verification: Optional[VerificationOut] = None`
(`backend/app/schemas/verification.py`). Aucun champ existant renommé ou
supprimé — un front qui ignore `verification` continue de fonctionner à
l'identique. Le Chat juridique reçoit le même bloc via un événement SSE
additif `event: verification`, envoyé juste avant `event: done`.

## 6. Statuts de confiance affichés (§7)

- `VERIFIE` (✓) — la ou les sources disponibles étayent suffisamment l'affirmation.
- `A_VERIFIER` (⚠) — pertinent mais nécessite une vérification complémentaire.
- `INCERTAIN` (?) — les éléments disponibles ne permettent pas de conclure.

Toujours accompagnés, côté front (`VerificationPanel.tsx`), du rappel
explicite : « plusieurs contrôles indépendants aident à repérer les erreurs
et les incertitudes — ils ne garantissent pas que cette analyse est
exacte. » Jamais présenté comme une preuve d'exactitude.

## 7. Suivi d'implémentation

- ✅ 5 agents ajoutés à `analyse.py` (prompts + fonctions), aucune fonction existante modifiée.
- ✅ `backend/app/security_guard.py` (sécurité) et `backend/app/quality_pipeline.py` (qualité + orchestration), strictement séparés.
- ✅ Contrôle déterministe des citations avec autorité forcée en code (pas seulement par prompt) — `_appliquer_autorite_deterministe` / `_recalculer_statut_global`.
- ✅ Câblé sur `/api/analyse/conclusions`, `/plan`, `/simulateur`, `/api/jurisprudence/consulter` (pipeline complet), `/api/chat/stream` (pipeline conversationnel dynamique), `/api/chat/contextuel` (garde-fou seul). `rapport-complet` volontairement laissé de côté (voir §2).
- ✅ Schémas additifs (`VerificationOut`), aucune régression sur les schémas existants.
- ✅ Front : section garde-fou de la LandingPage refaite en présentation à 5 badges ; `VerificationPanel.tsx` (additif) sur les 4 pages du pipeline complet + Chat juridique.
- ✅ Tests : `test_security_guard.py`, `test_quality_pipeline.py` (mécanique déterministe et dégradation, sans dépendance réseau), `test_chat_contextuel.py` adapté (le garde-fou s'exécute désormais avant `traiter_message_edition`). 91 tests backend verts, `tsc --noEmit` et `vite build` propres.
- ✅ Vérifié depuis avec de vrais appels API (clé réelle, pas de mocks) sur les 3 pipelines : `/api/analyse/conclusions` (vérificateur complet, citation absente correctement `NON_VERIFIE`), `/api/jurisprudence/consulter` (le critique a produit une vraie critique substantielle sur un agent principal trop prudent), `/api/chat/stream` (l'intention a bien déclenché le trio sur une question de fond, qui a détecté deux numéros d'arrêt inventés). Deux bugs réels trouvés et corrigés à cette occasion :
  - Le garde-fou rejetait à tort les messages courts/informels ("Bonjour") comme hors périmètre — corrigé par un court-circuit déterministe (≤ 25 caractères) + reformulation du prompt.
  - Le timeout par agent qualité (20s) était trop court pour des analyses substantielles, faisant systématiquement dégrader vérificateur/critique alors que l'agent principal avait le temps d'aboutir — porté à 45s.
- ⚠️ Un aller-retour complet du pipeline conversationnel (garde-fou + intention + génération + trio) peut prendre plus de 2 minutes sur une question de fond — cohérent avec le choix assumé de privilégier la profondeur à la vitesse sur ce cas précis (voir §2), mais à garder en tête pour l'expérience utilisateur du Chat.

## 8. Recommandations pour la suite

- Injection en place d'une balise `[VERIF:...]` (voir `analyse.REGLE_BALISAGE_CITATIONS`, via le moteur générique de `chat_actions`) pour les citations `NON_VERIFIE` que le modèle n'a pas déjà signalées lui-même.
- Persistance en base des traces de vérification (`quality_pipeline.EtapeTrace`), actuellement en mémoire seulement.
- Étalonnage d'un modèle plus rapide/économique pour le garde-fou et la couche LLM du vérificateur, une fois un id de modèle plus léger confirmé disponible côté clé API.
- Étendre le pipeline conversationnel dynamique au Chat contextuel pour les intentions `explain`/`compare` portant sur une vérification de jurisprudence ou une critique de stratégie.
