"""
test_export.py — Conversion des balises de références juridiques
([ART:...]/[JURISPRUDENCE:...]/[VERIF:...], voir analyse.REGLE_BALISAGE_CITATIONS)
en texte lisible pour les documents Word/PDF exportés (export.py) --
contrairement au front (RichOutput.tsx), un document exporté est une page
statique, la syntaxe brute d'une balise y serait illisible."""

import export


def test_rendre_balises_lisibles_convertit_une_balise_art():
    texte = "Le principe [ART:132-24:CP] impose au juge de tenir compte des éléments."
    assert export._rendre_balises_lisibles(texte) == "Le principe art. 132-24 du Code pénal impose au juge de tenir compte des éléments."


def test_rendre_balises_lisibles_convertit_une_balise_jurisprudence():
    texte = "[JURISPRUDENCE:Cass. Crim., 12 mars 2023, n°22-84.123] le confirme."
    assert export._rendre_balises_lisibles(texte) == "Cass. Crim., 12 mars 2023, n°22-84.123 le confirme."


def test_rendre_balises_lisibles_convertit_une_balise_verif_en_ancien_marqueur():
    """[VERIF:...] redevient "À VÉRIFIER" en texte libre à l'export -- seul
    format reconnaissable sur une page imprimée, sans interaction possible
    comme sur le front."""
    texte = "Un point [VERIF:absence de rapport d'enquête de personnalité au dossier] reste incertain."
    assert export._rendre_balises_lisibles(texte) == (
        "Un point [À VÉRIFIER : absence de rapport d'enquête de personnalité au dossier] reste incertain."
    )


def test_rendre_balises_lisibles_code_non_reconnu_reste_affiche_tel_quel():
    assert export._rendre_balises_lisibles("[ART:1:XYZ]") == "art. 1 du XYZ"


def test_rendre_balises_lisibles_texte_vide_ou_none():
    assert export._rendre_balises_lisibles("") == ""
    assert export._rendre_balises_lisibles(None) is None


def test_nettoyer_balises_est_recursif_sur_dict_et_liste():
    donnees = {
        "arguments": [
            {"piste": "Voir [ART:1240:CCIV]."},
            {"piste": "Non balisé, inchangé."},
        ],
        "points_attention": ["[VERIF:élément à confirmer]"],
    }
    nettoye = export._nettoyer_balises(donnees)
    assert nettoye["arguments"][0]["piste"] == "Voir art. 1240 du Code civil."
    assert nettoye["arguments"][1]["piste"] == "Non balisé, inchangé."
    assert nettoye["points_attention"] == ["[À VÉRIFIER : élément à confirmer]"]


def test_nettoyer_balises_supporte_none():
    assert export._nettoyer_balises(None) is None
