"""
test_recherche_cache.py — Chantier "temps de traitement des générations",
§2f : cache en mémoire des recherches Légifrance/Judilibre identiques
pendant une session, et §2b : le garde-fou et la recherche de jurisprudence
tournent en parallèle plutôt qu'en séquence dans /api/jurisprudence/consulter.
"""

import legifrance
import recherche_juridique
import judilibre


def setup_function():
    """Le cache est un dict au niveau module -- vidé avant chaque test pour
    ne jamais dépendre de l'ordre d'exécution des tests."""
    recherche_juridique._CACHE_RECHERCHE.clear()


def test_deuxieme_recherche_identique_ne_reinterroge_pas_les_sources(monkeypatch):
    appels_legifrance = []
    appels_judilibre = []
    monkeypatch.setattr(legifrance, "rechercher_articles", lambda query, max_results=5: appels_legifrance.append(query) or [{"reference": "art. 1", "texte": "...", "source": "Légifrance"}])
    monkeypatch.setattr(judilibre, "collecter_jurisprudence", lambda query, max_results=10: appels_judilibre.append(query) or [])

    resultat_1 = recherche_juridique.rechercher_contexte_juridique("rupture abusive du contrat")
    resultat_2 = recherche_juridique.rechercher_contexte_juridique("rupture abusive du contrat")

    assert len(appels_legifrance) == 1
    assert len(appels_judilibre) == 1
    assert resultat_1 == resultat_2


def test_requete_normalisee_avant_mise_en_cache(monkeypatch):
    """Deux requêtes qui ne différent que par la casse ou les espaces
    partagent la même entrée de cache."""
    appels = []
    monkeypatch.setattr(legifrance, "rechercher_articles", lambda query, max_results=5: appels.append(query) or [{"reference": "art. 1", "texte": "...", "source": "Légifrance"}])
    monkeypatch.setattr(judilibre, "collecter_jurisprudence", lambda query, max_results=10: [])

    recherche_juridique.rechercher_contexte_juridique("  Rupture Abusive  ")
    recherche_juridique.rechercher_contexte_juridique("rupture abusive")

    assert len(appels) == 1


def test_requete_differente_reinterroge_les_sources(monkeypatch):
    appels = []
    monkeypatch.setattr(legifrance, "rechercher_articles", lambda query, max_results=5: appels.append(query) or [{"reference": "art. 1", "texte": "...", "source": "Légifrance"}])
    monkeypatch.setattr(judilibre, "collecter_jurisprudence", lambda query, max_results=10: [])

    recherche_juridique.rechercher_contexte_juridique("licenciement abusif")
    recherche_juridique.rechercher_contexte_juridique("rupture de contrat")

    assert len(appels) == 2


def test_resultat_entierement_vide_nest_pas_mis_en_cache(monkeypatch):
    """Un résultat vide (souvent une panne transitoire) n'est jamais mis en
    cache -- sinon une requête identique resterait bloquée sur "aucun
    résultat" pendant toute la durée du TTL."""
    appels = []
    monkeypatch.setattr(legifrance, "rechercher_articles", lambda query, max_results=5: appels.append(query) or [])
    monkeypatch.setattr(judilibre, "collecter_jurisprudence", lambda query, max_results=10: [])

    recherche_juridique.rechercher_contexte_juridique("requête sans aucun résultat")
    recherche_juridique.rechercher_contexte_juridique("requête sans aucun résultat")

    assert len(appels) == 2  # jamais servi depuis un cache vide -- réessayé chaque fois
