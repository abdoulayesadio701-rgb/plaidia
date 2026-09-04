"""
recherche_juridique.py — Interroge en direct les API publiques françaises
(Légifrance pour les textes de loi, Judilibre pour la jurisprudence) afin
d'enrichir une analyse de plaidoirie à la volée, sans base de données
intermédiaire.

C'est le point d'entrée principal pour la recherche juridique en ligne.
"""

import concurrent.futures

import legifrance
import judilibre

TIMEOUT_DUR_PAR_SOURCE = 12  # secondes — limite absolue, indépendante des timeouts internes


def _appel_avec_timeout(fonction, *args, **kwargs):
    """Exécute fonction(*args, **kwargs) avec une limite de temps stricte.
    Protège contre les blocages réseau silencieux (DNS bloqué, pare-feu muet)
    que les timeouts internes de `requests` ne couvrent pas toujours.

    Important : n'attend PAS la fin du thread en arrière-plan après un
    timeout — sinon un blocage réseau reste bloquant malgré tout."""
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fonction, *args, **kwargs)
    try:
        return future.result(timeout=TIMEOUT_DUR_PAR_SOURCE)
    finally:
        executor.shutdown(wait=False)


def rechercher_contexte_juridique(query: str, max_par_source: int = 5) -> dict:
    """
    Interroge Légifrance et Judilibre en direct pour une requête donnée,
    EN PARALLÈLE (pas l'un après l'autre) — dans le pire cas (les deux
    lentes), l'attente totale reste plafonnée à 12 secondes, pas 24.

    Retourne {"articles_loi": [...], "jurisprudence": [...]}.

    Chaque source est interrogée indépendamment, avec une limite de temps
    stricte de 12 secondes : si l'une échoue, est trop lente, ou reste
    bloquée (réseau filtré, DNS muet...), l'autre continue de fonctionner
    et la fonction se termine toujours.
    """
    articles_loi = []
    jurisprudence_resultats = []

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    try:
        future_legifrance = executor.submit(legifrance.rechercher_articles, query, max_results=max_par_source)
        future_judilibre = executor.submit(judilibre.collecter_jurisprudence, query, max_results=max_par_source)

        try:
            articles_loi = future_legifrance.result(timeout=TIMEOUT_DUR_PAR_SOURCE)
        except concurrent.futures.TimeoutError:
            print(f"[avertissement] Légifrance indisponible : délai dépassé ({TIMEOUT_DUR_PAR_SOURCE}s) — réseau probablement bloqué ou trop lent.")
        except Exception as e:
            print(f"[avertissement] Légifrance indisponible : {e}")

        try:
            jurisprudence_resultats = future_judilibre.result(timeout=TIMEOUT_DUR_PAR_SOURCE)
        except concurrent.futures.TimeoutError:
            print(f"[avertissement] Judilibre indisponible : délai dépassé ({TIMEOUT_DUR_PAR_SOURCE}s) — réseau probablement bloqué ou trop lent.")
        except Exception as e:
            print(f"[avertissement] Judilibre indisponible : {e}")
    finally:
        executor.shutdown(wait=False)

    return {"articles_loi": articles_loi, "jurisprudence": jurisprudence_resultats}


def formater_contexte_pour_prompt(contexte: dict) -> str:
    """
    Transforme le résultat de rechercher_contexte_juridique() en un bloc de
    texte injectable dans le prompt d'analyse — toujours avec la source,
    jamais présenté comme une vérité absolue non sourcée.
    """
    parts = []

    if contexte["articles_loi"]:
        parts.append("Articles de loi trouvés en recherche live (Légifrance) :")
        for a in contexte["articles_loi"]:
            parts.append(f"- {a['reference']} : {a['texte']} (source : {a['source']})")

    if contexte["jurisprudence"]:
        parts.append("\nJurisprudence trouvée en recherche live (Judilibre) :")
        for j in contexte["jurisprudence"]:
            parts.append(f"- {j['reference']} : {j['resume']} (source : {j['source']})")

    if not parts:
        return ""

    return (
        "\n\nÉléments trouvés par recherche en ligne (non validés manuellement — "
        "à vérifier avant citation en plaidoirie) :\n" + "\n".join(parts)
    )
