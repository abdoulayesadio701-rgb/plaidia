"""
quality_pipeline.py — Orchestrateur + agents de QUALITÉ (vérificateur
juridique, contradicteur, validateur final), voir ARCHITECTURE_MULTI_AGENTS.md
§4-6, §8, §9.

Séparation stricte sécurité / qualité : ce module ne contient AUCUNE
décision d'autorisation/refus d'une demande (ça, c'est security_guard.py) --
seulement le contrôle de ce qu'un agent principal a déjà produit.

Deux pipelines, pas un seul appliqué partout (§9 : ne pas exécuter tous les
agents systématiquement) :

- `executer_pipeline_complet()` : garde-fou -> agent principal -> trio
  qualité, pour les fonctionnalités à formulaire fixe où la tâche est déjà
  connue par l'endpoint appelé (conclusions, plan, simulateur, consultation
  de jurisprudence) -- pas d'agent d'intention ici, il serait redondant.
- `executer_garde_fou_et_intention()` + `executer_trio_qualite_si_necessaire()` :
  pour le Chat juridique, seul endroit où la tâche n'est pas connue à
  l'avance -- l'agent d'intention détermine dynamiquement si le trio
  qualité est nécessaire.

Le trio qualité est TOUJOURS encapsulé par `_appel_protege` (même idiome que
`recherche_juridique._appel_avec_timeout` : ThreadPoolExecutor + timeout
strict) : un agent qualité lent ou en échec ne fait jamais échouer la
requête -- le résultat principal est renvoyé tel quel, `verification`
dégradée plutôt qu'absente. Aucun agent qualité ne peut casser une
fonctionnalité qui marchait avant ce chantier.
"""

import concurrent.futures
import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable

import analyse as legacy_analyse

from app.security_guard import DemandeRefusee, executer_garde_fou  # noqa: F401  (DemandeRefusee ré-exportée pour les routers/tests)

_TIMEOUT_AGENT_QUALITE = 45  # secondes -- par agent (vérificateur, critique, validateur), indépendamment les uns des autres.

REGLE_POSTURE_STRATEGIQUE = (
    "Règle posture stratégique obligatoire : signale toute recommandation qui minimise un fait défavorable au client, "
    "déforme une source ou promet un résultat. Fais apparaître clairement les points faibles du client et distingue "
    "toujours le diagnostic neutre de la stratégie pour la partie représentée. Limite absolue, non négociable : "
    "aucune suggestion d'altérer, cacher ou fabriquer un fait ou une pièce, de tromper le tribunal ou de citer une "
    "source déformée -- une telle suggestion doit toujours être signalée comme franchissant cette ligne (critique "
    "de type 'limite_deontologique_franchie', gravité 'Élevée'), jamais laissée passer silencieusement."
)
# 20s (valeur initiale) s'est révélé trop court à l'usage réel : sur une
# analyse de conclusions substantielle (constaté avec un vrai appel API),
# le vérificateur et le critique tombaient systématiquement en dégradation
# (repli déterministe, critiques toujours vides) alors que l'appel
# principal, lui, avait le temps d'aboutir -- un pipeline "complet" qui
# dégrade presque toujours son étage qualité perd l'essentiel de sa valeur.
# Un total de plusieurs dizaines de secondes reste acceptable : ce pipeline
# n'est réservé qu'aux analyses à fort enjeu (voir §2 ARCHITECTURE_MULTI_AGENTS.md),
# où l'utilisateur attend déjà une réponse approfondie, pas instantanée.


def _log(message: str) -> None:
    print(f"[quality_pipeline] {message}", flush=True)


# --- Contrôle déterministe des citations (couche code de l'agent vérificateur, §4) ---
# Balisage structuré des références juridiques (demande explicite de
# l'utilisateur -- voir analyse.REGLE_BALISAGE_CITATIONS, injectée dans les
# prompts système qui produisent des citations) : remplace l'ancien
# marqueur libre "À VÉRIFIER : " par [ART:<numéro>:<code>],
# [JURISPRUDENCE:<référence>] et [VERIF:<description>]. Les deux premières
# sont des citations à confronter aux sources ; [VERIF:...] est un aveu
# explicite d'incertitude du modèle -- jamais recontrôlé, exactement comme
# l'ancien préfixe "À VÉRIFIER" qu'il remplace (voir _verifier_citations).
_RE_TAG_ART = re.compile(r"\[ART:([^:\]]+):([A-Z]+)\]")
_RE_TAG_JURISPRUDENCE = re.compile(r"\[JURISPRUDENCE:([^\]]+)\]")
_RE_TAG_VERIF = re.compile(r"\[VERIF:([^\]]*)\]")
_RE_TAG_TOUTES = re.compile(r"\[(?:ART|JURISPRUDENCE|VERIF):[^\]]*\]")

# Extraction HEURISTIQUE (regex) HÉRITÉE, sans balise -- filet de sécurité
# pour du texte non balisé : documents générés avant ce chantier (stockés
# tels quels en base, jamais régénérés rétroactivement) ou citation que le
# modèle aurait malgré tout laissée sans balise. Ce n'est pas un parseur
# juridique complet : une citation non détectée ici n'est simplement pas
# contrôlée déterministiquement, elle n'est jamais pour autant considérée
# comme fausse (voir _verifier_citations).
_RE_CITATIONS = [
    re.compile(r"\bart(?:icle)?s?\.?\s*[A-Z]{0,2}\.?\s*\d+(?:[-.]\d+){0,3}", re.IGNORECASE),
    re.compile(r"\bCass\.?\s*(?:civ|soc|crim|com|ass\.?\s*pl[ée]n)\.?[^,\n]{0,40},?[^,\n]{0,60}\d{4}", re.IGNORECASE),
    re.compile(r"\bC\.?A\.?\s+[A-ZÉÈÀÂÎÔÛ][\wéèêàâîôûç'\-]+[^,\n]{0,40}\d{4}"),
    re.compile(r"\bn°\s*\d{1,2}[-./]\d{2,6}(?:[-.]\d+)?", re.IGNORECASE),
]


def _extraire_citations_balisees(texte: str) -> list[dict]:
    """Extrait les balises [ART:...]/[JURISPRUDENCE:...] présentes dans
    `texte` -- une entrée par balise, avec sa forme brute (identité utilisée
    pour le repérage/l'affichage, voir frontend/src/components/RichOutput.tsx)
    et sa clé de recherche (numéro d'article ou référence de jurisprudence,
    utilisée pour la confrontation aux sources dans _verifier_citations).
    Les balises [VERIF:...] ne sont volontairement pas incluses ici : elles
    ne citent rien à confronter aux sources, voir _extraire_verif."""
    trouvees = []
    for m in _RE_TAG_ART.finditer(texte or ""):
        trouvees.append({"type": "ART", "brut": m.group(0), "cle_recherche": m.group(1).strip()})
    for m in _RE_TAG_JURISPRUDENCE.finditer(texte or ""):
        trouvees.append({"type": "JURISPRUDENCE", "brut": m.group(0), "cle_recherche": m.group(1).strip()})
    return trouvees


def _extraire_verif(texte: str) -> list[str]:
    """Descriptions des balises [VERIF:...] présentes dans `texte`, dans
    l'ordre d'apparition -- l'équivalent structuré de l'ancien
    "À VÉRIFIER : <description>" en texte libre."""
    return [m.group(1).strip() for m in _RE_TAG_VERIF.finditer(texte or "")]


def _extraire_citations(texte: str) -> list[str]:
    """Filet heuristique hérité (voir le commentaire au-dessus de
    _RE_CITATIONS) -- n'analyse le texte qu'une fois les balises retirées,
    pour ne jamais compter deux fois la même citation (le contenu d'une
    balise [JURISPRUDENCE:Cass. Crim....] correspondrait sinon aussi à ce
    regex)."""
    texte_sans_balises = _RE_TAG_TOUTES.sub(" ", texte or "")
    trouvees: set[str] = set()
    for regex in _RE_CITATIONS:
        for m in regex.finditer(texte_sans_balises):
            trouvees.add(m.group(0).strip())
    return sorted(trouvees)


def _normaliser(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _verifier_citations(texte: str, sources_textes: list[str]) -> list[dict]:
    """Contrôle déterministe (§4, couche code) : chaque citation -- balisée
    ([ART:...]/[JURISPRUDENCE:...], voie normale depuis ce chantier) ou
    détectée par le filet heuristique hérité (texte non balisé) -- est
    cherchée (normalisée) dans `sources_textes` (textes des sources
    réellement fournies au modèle principal -- recherche live, corpus
    validé, ou le texte source original selon la fonctionnalité). Une
    balise [VERIF:...] n'est jamais recontrôlée : c'est un aveu explicite
    d'incertitude du modèle, pas une citation dissimulée -- exactement
    comme l'ancien préfixe "À VÉRIFIER" qu'elle remplace (voir
    _extraire_verif). Pour le filet hérité, la même règle s'applique via le
    préfixe textuel "à vérifier" resté dans les documents antérieurs à ce
    chantier.

    Ce filtre ne peut jamais être contourné par la couche LLM du
    vérificateur (analyse.verifier_juridiquement), à qui son verdict est
    transmis comme une contrainte, pas une suggestion."""
    bloc_source_normalise = _normaliser(" ".join(sources_textes))

    def _statut(cle_recherche: str) -> str:
        if not bloc_source_normalise:
            return "AUCUNE_SOURCE"
        return "VERIFIE" if _normaliser(cle_recherche) in bloc_source_normalise else "NON_VERIFIE"

    resultats = [
        {"citation": c["brut"], "statut_deterministe": _statut(c["cle_recherche"])}
        for c in _extraire_citations_balisees(texte)
    ]

    for citation in _extraire_citations(texte):
        pos = texte.find(citation)
        prefixe = texte[max(0, pos - 40):pos] if pos != -1 else ""
        if "à vérifier" in prefixe.lower() or "a verifier" in prefixe.lower():
            continue
        resultats.append({"citation": citation, "statut_deterministe": _statut(citation)})
    return resultats


def verifier_citations_deterministe(texte: str, sources_textes: list[str]) -> list[dict]:
    """Wrapper public de _verifier_citations -- même contrôle déterministe
    (agnostique au modèle qui a produit `texte`, voir _verifier_citations),
    exposé pour les routes qui n'ont pas de couche LLM vérificatrice dédiée
    (extraction, résumé -- voir app/routers/greffier.py et
    app/routers/analyse.py). Ne fait AUCUN appel réseau : ne remplace pas le
    trio qualité (verifier_juridiquement/critiquer_reponse/valider_finalement,
    réservé aux fonctions d'analyse/génération sur Claude), juste le filtre
    de premier niveau qui existait déjà pour elles."""
    return _verifier_citations(texte, sources_textes)


def _statut_deterministe_global(citations: list[dict]) -> str:
    statuts = [c["statut_deterministe"] for c in citations]
    if any(s == "NON_VERIFIE" for s in statuts):
        return "NON_VERIFIE"
    if not statuts:
        return "A_VERIFIER"
    if all(s == "VERIFIE" for s in statuts):
        return "VERIFIE"
    return "A_VERIFIER"


def _mapper_statut_deterministe(s: str) -> str:
    return {"VERIFIE": "VERIFIE", "NON_VERIFIE": "NON_VERIFIE", "AUCUNE_SOURCE": "A_VERIFIER"}.get(s, "A_VERIFIER")


def _mapper_verif_vers_confiance(statut_verif: str) -> str:
    if statut_verif == "NON_VERIFIE":
        return "INCERTAIN"
    if statut_verif == "VERIFIE":
        return "VERIFIE"
    return "A_VERIFIER"


def _appliquer_autorite_deterministe(elements: list[dict], citations: list[dict]) -> list[dict]:
    """Fait respecter EN CODE (pas seulement par instruction de prompt) la
    règle du §4 : le contrôle déterministe des citations fait autorité.
    Quoi que renvoie la couche LLM du vérificateur (analyse.verifier_juridiquement),
    un élément dont l'affirmation correspond à une citation classée
    NON_VERIFIE par le code ne peut jamais ressortir à un statut plus
    favorable -- y compris si le modèle "hallucine sa propre confirmation".
    Une citation NON_VERIFIE que le LLM aurait omise de ses `elements` est
    ajoutée plutôt que silencieusement perdue."""
    citations_non_verifiees = [c["citation"] for c in citations if c["statut_deterministe"] == "NON_VERIFIE"]
    if not citations_non_verifiees:
        return elements

    def _correspond(affirmation: str, citation: str) -> bool:
        a, c = affirmation.lower(), citation.lower()
        return bool(a) and bool(c) and (c in a or a in c)

    corriges = []
    couvertes: list[str] = []
    for el in elements:
        affirmation = el.get("affirmation", "")
        citation_liee = next((c for c in citations_non_verifiees if _correspond(affirmation, c)), None)
        if citation_liee and el.get("statut") != "NON_VERIFIE":
            el = {
                **el,
                "statut": "NON_VERIFIE",
                "commentaire": (
                    (el.get("commentaire", "") + " ").strip()
                    + " [Statut corrigé par le contrôle déterministe : citation absente des sources fournies.]"
                ).strip(),
            }
        if citation_liee:
            couvertes.append(citation_liee)
        corriges.append(el)

    for citation in citations_non_verifiees:
        if citation not in couvertes:
            corriges.append(
                {
                    "affirmation": citation,
                    "statut": "NON_VERIFIE",
                    "commentaire": "Citation absente des sources fournies (contrôle déterministe) -- non reprise explicitement par le vérificateur.",
                }
            )
    return corriges


def _recalculer_statut_global(statut_propose: str, elements: list[dict]) -> str:
    """Cohérence forcée entre `elements` et `statut_global` après le
    passage de _appliquer_autorite_deterministe : un statut_global
    "VERIFIE" alors qu'un élément est NON_VERIFIE serait incohérent et
    trompeur pour l'utilisateur."""
    if any(e.get("statut") == "NON_VERIFIE" for e in elements):
        return "NON_VERIFIE"
    return statut_propose


@dataclass
class EtapeTrace:
    agent: str
    statut: str  # "ok" | "degrade" | "ignore"
    duree_ms: int
    detail: str = ""


@dataclass
class ResultatPipeline:
    resultat_principal: object
    verification: dict | None
    trace: list[EtapeTrace] = field(default_factory=list)


def _ms(t0: float) -> int:
    return int((time.monotonic() - t0) * 1000)


def texte_pour_verification(resultat) -> str:
    """Sérialise le résultat de l'agent principal (dict structuré ou texte
    libre selon la fonctionnalité) en texte lisible par les agents
    qualité. Public : réutilisé par les endpoints en streaming (§2a du
    chantier "temps de traitement des générations"), qui appellent
    executer_trio_qualite() directement plutôt que executer_pipeline_complet()."""
    if isinstance(resultat, str):
        return resultat
    try:
        return json.dumps(resultat, ensure_ascii=False, indent=2)
    except TypeError:
        return str(resultat)


_ORDRE_GRAVITE = {"Faible": 0, "Moyenne": 1, "Élevée": 2}


def _gravite_max(critiques: list[dict]) -> str | None:
    if not critiques:
        return None
    return max(critiques, key=lambda c: _ORDRE_GRAVITE.get(c.get("gravite"), 0)).get("gravite")


def _verdicts_se_contredisent(resultat_verif: dict, resultat_critique: dict) -> bool:
    """Chantier "temps de traitement des générations", §2b : la validation
    finale ne rappelle le modèle (agent de validation finale) QUE si le
    vérificateur et le critique se contredisent réellement -- le vérificateur
    juge les citations fiables (VERIFIE) alors que le critique a relevé une
    faiblesse de gravité Élevée, que le vérificateur ne pouvait pas voir
    puisqu'il ne juge que les citations. Dans tous les autres cas, les deux
    verdicts pointent déjà dans la même direction et une fusion déterministe
    en code (_valider_finalement_deterministe) suffit, sans appel réseau
    supplémentaire."""
    return resultat_verif.get("statut_global") == "VERIFIE" and _gravite_max(resultat_critique.get("critiques", [])) == "Élevée"


def _valider_finalement_deterministe(resultat_verif: dict, resultat_critique: dict) -> dict:
    """Fusion EN CODE du vérificateur et du critique, sans appel au modèle
    (§2b) -- remplace l'agent de validation finale dans le cas courant où
    les deux verdicts ne se contredisent pas (voir _verdicts_se_contredisent).
    Reste aussi honnête que VALIDATION_FINALE_SYSTEM_PROMPT : jamais de
    statut plus favorable que ce que le vérificateur a établi, jamais de
    contenu juridique nouveau inventé."""
    confiance = _mapper_verif_vers_confiance(resultat_verif.get("statut_global", "A_VERIFIER"))
    critiques = resultat_critique.get("critiques", [])
    if critiques and confiance == "VERIFIE":
        # Une critique existe mais n'a pas déclenché de contradiction
        # (gravité non Élevée) -- reste honnête : ne jamais afficher VERIFIE
        # sans réserve si le contradicteur a quand même relevé un point.
        confiance = "A_VERIFIER"

    points_a_verifier = [
        e["affirmation"] for e in resultat_verif.get("elements", [])
        if e.get("statut") in ("NON_VERIFIE", "A_VERIFIER", "PARTIELLEMENT_VERIFIE")
    ]

    n_total = len(resultat_verif.get("elements", []))
    n_verifie = sum(1 for e in resultat_verif.get("elements", []) if e.get("statut") == "VERIFIE")
    phrases = []
    if n_total:
        phrases.append(f"{n_verifie}/{n_total} affirmation(s) vérifiée(s) par recoupement avec les sources.")
    else:
        phrases.append("Aucune citation détectée à recouper avec les sources.")
    if critiques:
        phrases.append(f"{len(critiques)} point(s) soulevé(s) par l'agent critique : {resultat_critique.get('synthese', '').strip() or 'voir le détail ci-dessous.'}")
    else:
        phrases.append("Aucune faiblesse notable relevée par l'agent critique.")

    return {
        "statut_global": confiance,
        "points_a_verifier": points_a_verifier,
        "points_forts": [],
        "synthese_utilisateur": " ".join(phrases),
    }


def log_trace(feature: str, trace: list[EtapeTrace]) -> None:
    """Journalise la durée de chaque étape du pipeline, et le total --
    chantier "temps de traitement des générations", §1 : mesure réelle, dans
    les logs backend, avant toute décision d'optimisation."""
    total = sum(e.duree_ms for e in trace)
    detail = " | ".join(f"{e.agent}={e.duree_ms}ms[{e.statut}]" for e in trace)
    _log(f"{feature} -- durée totale mesurée : {total}ms -- {detail}")


def _appel_protege(fonction: Callable[[], dict], valeur_repli: dict):
    """Exécute `fonction` avec un timeout strict, réutilisant l'idiome déjà
    établi par recherche_juridique._appel_avec_timeout (ThreadPoolExecutor à
    un seul worker, n'attend pas le thread après un timeout). Ne relance
    jamais d'exception : un agent qualité lent, en erreur, ou dont la clé
    API échoue dégrade proprement vers `valeur_repli` plutôt que de faire
    échouer toute la requête."""
    return _appels_proteges_en_parallele([(fonction, valeur_repli)])[0]


def _appels_proteges_en_parallele(taches: list[tuple[Callable[[], dict], dict]]) -> list[dict]:
    """Généralise _appel_protege à plusieurs agents lancés EN PARALLÈLE (un
    thread par tâche, même idiome que rapport_complet et
    recherche_juridique.rechercher_contexte_juridique) -- chantier "temps de
    traitement des générations", §2b : remplace un enchaînement séquentiel
    (vérificateur puis critique) par une exécution simultanée, où l'attente
    totale devient le max des durées individuelles, pas leur somme.

    Chaque tâche garde son propre timeout et son propre repli, indépendamment
    des autres -- un agent lent ou en échec ne bloque et ne dégrade jamais
    les autres."""
    if not taches:
        return []
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(taches))
    try:
        futures = [executor.submit(fonction) for fonction, _ in taches]
        resultats = []
        for future, (_, repli) in zip(futures, taches):
            try:
                resultats.append(future.result(timeout=_TIMEOUT_AGENT_QUALITE))
            except concurrent.futures.TimeoutError:
                _log(f"agent qualité : délai dépassé ({_TIMEOUT_AGENT_QUALITE}s) -- résultat dégradé utilisé.")
                resultats.append(repli)
            except Exception as e:
                _log(f"agent qualité en échec : {e} -- résultat dégradé utilisé.")
                resultats.append(repli)
        return resultats
    finally:
        executor.shutdown(wait=False)


def _executer_trio_qualite(texte: str, sources_textes: list[str], contexte_dossier: str, trace: list[EtapeTrace]) -> dict:
    """Étapes 3 à 5 (§4-6) : vérificateur juridique -> critique ->
    validation finale. Chaque étage est protégé indépendamment -- l'échec
    d'un agent ne bloque jamais les suivants, il dégrade seulement la
    précision du résultat."""
    citations = _verifier_citations(texte, sources_textes)
    contexte_sources = ("\n\n".join(t for t in sources_textes if t)[:8000] + "\n\n" + REGLE_POSTURE_STRATEGIQUE)

    repli_verif = {
        "statut_global": _statut_deterministe_global(citations),
        "elements": [
            {
                "affirmation": c["citation"],
                "statut": _mapper_statut_deterministe(c["statut_deterministe"]),
                "commentaire": "Vérification LLM indisponible -- statut basé sur le seul contrôle déterministe des sources.",
            }
            for c in citations
        ],
    }
    # §2b : vérificateur et critique n'ont besoin l'un de l'autre pour rien
    # -- lancés EN PARALLÈLE plutôt qu'en séquence, l'attente devient le max
    # des deux durées, pas leur somme.
    t0 = time.monotonic()
    repli_critique = {"critiques": [], "synthese": ""}
    resultat_verif, resultat_critique = _appels_proteges_en_parallele([
        (lambda: legacy_analyse.verifier_juridiquement(texte, citations, contexte_sources), repli_verif),
        (lambda: legacy_analyse.critiquer_reponse(texte, f"{contexte_dossier}\n\n{REGLE_POSTURE_STRATEGIQUE}"), repli_critique),
    ])
    duree_parallele = _ms(t0)
    trace.append(EtapeTrace("legal_verifier", "ok" if resultat_verif is not repli_verif else "degrade", duree_parallele))
    trace.append(EtapeTrace("critic_agent", "ok" if resultat_critique is not repli_critique else "degrade", duree_parallele))

    # Le contrôle déterministe fait autorité EN CODE, pas seulement par
    # instruction de prompt -- s'applique que resultat_verif vienne d'un
    # vrai appel LLM ou du repli déterministe ci-dessus (idempotent dans ce
    # second cas).
    elements_corriges = _appliquer_autorite_deterministe(resultat_verif.get("elements", []), citations)
    resultat_verif = {
        **resultat_verif,
        "elements": elements_corriges,
        "statut_global": _recalculer_statut_global(resultat_verif.get("statut_global", "A_VERIFIER"), elements_corriges),
    }

    # §2b : la validation finale est désormais une fusion déterministe en
    # code (_valider_finalement_deterministe), sans appel au modèle -- sauf
    # si les deux verdicts se contredisent (_verdicts_se_contredisent), seul
    # cas où un arbitrage par le modèle reste justifié.
    t0 = time.monotonic()
    if _verdicts_se_contredisent(resultat_verif, resultat_critique):
        repli_final = {
            "statut_global": _mapper_verif_vers_confiance(resultat_verif.get("statut_global", "A_VERIFIER")),
            "points_a_verifier": [
                e["affirmation"] for e in resultat_verif.get("elements", []) if e.get("statut") in ("NON_VERIFIE", "A_VERIFIER")
            ],
            "points_forts": [],
            "synthese_utilisateur": "Validation finale indisponible -- statut basé sur le vérificateur juridique seul.",
        }
        resultat_final = _appel_protege(lambda: legacy_analyse.valider_finalement(resultat_verif, resultat_critique), repli_final)
        trace.append(EtapeTrace("final_validator", "ok" if resultat_final is not repli_final else "degrade", _ms(t0), "verdicts contradictoires -- arbitrage par le modèle"))
    else:
        resultat_final = _valider_finalement_deterministe(resultat_verif, resultat_critique)
        trace.append(EtapeTrace("final_validator", "deterministe", _ms(t0)))

    return {
        "statut_global": resultat_final.get("statut_global", "A_VERIFIER"),
        "elements": resultat_verif.get("elements", []),
        "critiques": resultat_critique.get("critiques", []),
        "points_a_verifier": resultat_final.get("points_a_verifier", []),
        "synthese_utilisateur": resultat_final.get("synthese_utilisateur", ""),
    }


def executer_trio_qualite(texte: str, sources_textes: list[str] | None = None, contexte_dossier: str = "") -> tuple[dict, list[EtapeTrace]]:
    """Point d'entrée public du trio qualité seul, sans garde-fou ni agent
    principal -- utilisé par les endpoints en streaming (§2a du chantier
    "temps de traitement des générations"), qui ont déjà émis le résultat de
    l'agent principal et n'attendent plus que les statuts de vérification."""
    trace: list[EtapeTrace] = []
    verification = _executer_trio_qualite(texte, sources_textes or [], contexte_dossier, trace)
    return verification, trace


def executer_pipeline_complet(
    feature: str,
    texte_a_screener: str,
    fonction_principale: Callable[[], object],
    *,
    sources_textes: list[str] | None = None,
    contexte_dossier: str = "",
    garde_fou_precalcule: dict | None = None,
) -> ResultatPipeline:
    """Pipeline complet (§9, diagramme cible) : garde-fou d'entrée -> agent
    principal (inchangé) -> trio qualité. Réservé aux fonctionnalités à
    formulaire fixe et fort enjeu de citations (conclusions, plan,
    simulateur, consultation de jurisprudence) -- voir
    ARCHITECTURE_MULTI_AGENTS.md pour la classification complète.

    `garde_fou_precalcule` (chantier "temps de traitement", §2b) : si fourni,
    le garde-fou n'est PAS réexécuté -- utilisé quand l'appelant l'a déjà
    lancé EN PARALLÈLE d'une autre étape indépendante (ex. la recherche
    Légifrance/Judilibre dans /api/jurisprudence/consulter, voir
    routers/jurisprudence.py) plutôt que de l'attendre en tête de pipeline.

    Lève security_guard.DemandeRefusee si le garde-fou refuse la demande --
    à laisser remonter tel quel, géré par main.py comme toute autre
    exception métier."""
    trace: list[EtapeTrace] = []

    if garde_fou_precalcule is not None:
        trace.append(EtapeTrace("garde_fou_entree", "ok", 0, garde_fou_precalcule.get("reason", "") + " (parallélisé avec une autre étape)"))
    else:
        t0 = time.monotonic()
        garde = executer_garde_fou(texte_a_screener)
        trace.append(EtapeTrace("garde_fou_entree", "ok", _ms(t0), garde.get("reason", "")))

    t0 = time.monotonic()
    resultat_principal = fonction_principale()
    trace.append(EtapeTrace("agent_principal", "ok", _ms(t0)))

    texte_verif = texte_pour_verification(resultat_principal)
    verification = _executer_trio_qualite(texte_verif, sources_textes or [], contexte_dossier, trace)

    log_trace(feature, trace)
    return ResultatPipeline(resultat_principal=resultat_principal, verification=verification, trace=trace)


def executer_strategie_combative(fonction_strategie: Callable[[], dict]) -> dict:
    """Protège l'appel à l'agent de stratégie combative (complément
    posture/stratégie -- voir analyse.generer_strategie_combative) avec le
    même idiome que le trio qualité (_appel_protege) : un agent lent ou en
    échec ne casse jamais l'endpoint. La stratégie retombe alors sur le
    texte générique construit par app.deps.structurer_sortie_strategique,
    jamais sur une erreur 500."""
    return _appel_protege(fonction_strategie, {"moyens": [], "reponses_arguments_adverses": []})


def executer_garde_fou_et_intention(message: str, historique: list[dict] | None = None) -> tuple[dict, dict]:
    """Étapes 1-2 du pipeline conversationnel (§10) pour le Chat juridique :
    garde-fou puis agent d'intention. Lève DemandeRefusee si le garde-fou
    refuse. Retourne (evaluation_garde_fou, intention) -- c'est le seul
    endroit où l'agent d'intention est utile : la tâche n'est pas connue à
    l'avance, contrairement aux endpoints à formulaire fixe."""
    evaluation = executer_garde_fou(message)
    intention = legacy_analyse.analyser_intention_juridique(message, historique)
    return evaluation, intention


def executer_trio_qualite_si_necessaire(
    texte_reponse: str, intention: dict, sources_textes: list[str] | None = None, contexte_dossier: str = ""
) -> dict | None:
    """Étapes 3-5 du pipeline conversationnel, exécutées SEULEMENT si
    intention['necessite_verification_approfondie'] est vrai -- profondeur
    dynamique demandée en §9/§10 : une question conversationnelle simple
    n'appelle aucun agent qualité supplémentaire, aucun appel superflu."""
    if not intention.get("necessite_verification_approfondie"):
        return None
    trace: list[EtapeTrace] = []
    verification = _executer_trio_qualite(texte_reponse, sources_textes or [], contexte_dossier, trace)
    log_trace("chat", trace)
    return verification
