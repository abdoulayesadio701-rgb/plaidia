"""
test_recherche_lexicometrique.py — Recherche jurisprudentielle par
similarité lexicométrique déterministe (voir recherche_lexicometrique.py).

Aucun appel réseau ni LLM ici : chaque test vérifie un calcul réel sur du
texte, conformément à la consigne ("zéro invention... chaque chiffre doit
provenir d'un calcul réel, jamais d'une estimation").
"""

import pytest

import recherche_lexicometrique as lex


# --- _tokeniser ---------------------------------------------------------

def test_tokeniser_minuscule_et_retire_les_mots_vides():
    tokens = lex._tokeniser("Le défendeur invoque la prescription de l'article.")
    assert "le" not in tokens
    assert "la" not in tokens
    assert "de" not in tokens
    assert "défendeur" in tokens
    assert "prescription" in tokens
    assert "article" in tokens


def test_tokeniser_garde_les_accents_et_les_mots_composes():
    tokens = lex._tokeniser("La mise-en-demeure précède la responsabilité.")
    assert "mise-en-demeure" in tokens
    assert "responsabilité" in tokens


def test_tokeniser_texte_vide_ou_none():
    assert lex._tokeniser("") == []
    assert lex._tokeniser(None) == []


# --- _similarite_cosinus -------------------------------------------------

def test_similarite_cosinus_vecteurs_identiques_vaut_un():
    from collections import Counter
    v = Counter({"prescription": 2, "contrat": 1})
    assert lex._similarite_cosinus(v, v) == pytest.approx(1.0)


def test_similarite_cosinus_aucun_terme_commun_vaut_zero():
    from collections import Counter
    a = Counter({"prescription": 1})
    b = Counter({"contrat": 1})
    assert lex._similarite_cosinus(a, b) == 0.0


def test_similarite_cosinus_vecteur_vide_vaut_zero():
    from collections import Counter
    assert lex._similarite_cosinus(Counter(), Counter({"contrat": 1})) == 0.0


# --- comparer_a_la_jurisprudence_validee ---------------------------------

def _decision(reference, resume):
    return {"reference": reference, "resume": resume, "domaine": "civil", "source": "test", "validee": 1}


def test_ecarte_les_decisions_sous_le_seuil_de_pertinence(monkeypatch):
    monkeypatch.setattr(lex.db, "get_jurisprudence_validee", lambda domaine=None: [
        _decision("Cass. Civ., decision proche", "prescription extinctive de l'action en responsabilité contractuelle"),
        _decision("Cass. Soc., decision eloignee", "licenciement pour faute grave et indemnite de preavis"),
    ])
    resultats = lex.comparer_a_la_jurisprudence_validee(
        "L'action en responsabilité contractuelle est prescrite par l'effet de la prescription extinctive."
    )
    references = [r["reference"] for r in resultats]
    assert "Cass. Civ., decision proche" in references
    assert "Cass. Soc., decision eloignee" not in references


def test_classe_du_plus_pertinent_au_moins_pertinent(monkeypatch):
    monkeypatch.setattr(lex.db, "get_jurisprudence_validee", lambda domaine=None: [
        _decision("A", "prescription extinctive responsabilité contractuelle"),
        _decision("B", "prescription extinctive responsabilité contractuelle dommage prejudice reparation"),
    ])
    resultats = lex.comparer_a_la_jurisprudence_validee(
        "prescription extinctive responsabilité contractuelle dommage prejudice reparation"
    )
    assert len(resultats) == 2
    assert resultats[0]["rang"] == 1
    assert resultats[1]["rang"] == 2
    assert resultats[0]["taux_similarite"] >= resultats[1]["taux_similarite"]
    # La décision B partage plus de termes avec le texte de départ -> doit sortir en tête.
    assert resultats[0]["reference"] == "B"


def test_termes_cles_partages_contiennent_bien_du_vocabulaire_commun(monkeypatch):
    monkeypatch.setattr(lex.db, "get_jurisprudence_validee", lambda domaine=None: [
        _decision("A", "prescription extinctive de la responsabilité contractuelle"),
    ])
    resultats = lex.comparer_a_la_jurisprudence_validee(
        "prescription extinctive de la responsabilité contractuelle"
    )
    assert resultats[0]["termes_cles_partages"]
    assert "prescription" in resultats[0]["termes_cles_partages"]


def test_liste_vide_si_base_de_jurisprudence_vide(monkeypatch):
    monkeypatch.setattr(lex.db, "get_jurisprudence_validee", lambda domaine=None: [])
    assert lex.comparer_a_la_jurisprudence_validee("un argument quelconque") == []


def test_liste_vide_si_aucune_decision_ne_depasse_le_seuil(monkeypatch):
    monkeypatch.setattr(lex.db, "get_jurisprudence_validee", lambda domaine=None: [
        _decision("A", "licenciement pour faute grave et indemnite de preavis"),
    ])
    assert lex.comparer_a_la_jurisprudence_validee("prescription extinctive responsabilité contractuelle") == []


def test_le_domaine_est_transmis_a_la_requete_db(monkeypatch):
    appels = []

    def _espion(domaine=None):
        appels.append(domaine)
        return []

    monkeypatch.setattr(lex.db, "get_jurisprudence_validee", _espion)
    lex.comparer_a_la_jurisprudence_validee("texte", domaine="social")
    assert appels == ["social"]


# --- formater_resultats ---------------------------------------------------

def test_formater_resultats_respecte_le_format_exact():
    resultats = [
        {"rang": 1, "reference": "Cass. Civ., 1re, 12 mars 2020, n°19-12.345", "taux_similarite": 72.3, "termes_cles_partages": ["prescription", "contractuelle"]},
    ]
    assert lex.formater_resultats(resultats) == (
        "[1] - [Cass. Civ., 1re, 12 mars 2020, n°19-12.345] - [72.3%] - [prescription, contractuelle]"
    )


def test_formater_resultats_signale_explicitement_labsence_de_correspondance():
    texte = lex.formater_resultats([])
    assert "50" in texte
    assert "aucune" in texte.lower()
