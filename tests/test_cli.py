"""test_cli.py — Détection des points [VERIF:...] dans les résultats du CLI
(cli.py), remplace l'ancien marqueur libre "À VÉRIFIER" -- voir
analyse.REGLE_BALISAGE_CITATIONS."""

import cli


def test_contient_point_a_verifier_detecte_la_balise():
    assert cli._contient_point_a_verifier("Un point [VERIF:référence à confirmer] reste incertain.") is True


def test_contient_point_a_verifier_detecte_le_marqueur_herite():
    assert cli._contient_point_a_verifier("À VÉRIFIER : article non confirmé.") is True


def test_contient_point_a_verifier_faux_si_absent():
    assert cli._contient_point_a_verifier("Rien à signaler ici.") is False


def test_extraire_a_verifier_analyse_recupere_les_pistes_balisees():
    result = {
        "arguments": [
            {"refutations": [
                {"angle": "Juridique", "piste": "[VERIF:rechercher un arrêt en ce sens]"},
                {"angle": "Factuel", "piste": "Produire l'attestation."},
            ]}
        ]
    }
    items = cli._extraire_a_verifier_analyse(result)
    assert items == ["[VERIF:rechercher un arrêt en ce sens]"]


def test_extraire_a_verifier_plan_recupere_les_notes_balisees():
    plan = {"plan": [{"notes": "[VERIF:vérifier la jurisprudence applicable]"}, {"notes": "Notes ordinaires."}]}
    assert cli._extraire_a_verifier_plan(plan) == ["[VERIF:vérifier la jurisprudence applicable]"]


def test_extraire_a_verifier_simulateur_recupere_les_pistes_balisees():
    result = {"objections": [{"piste_reponse": "[VERIF:citer un arrêt si disponible]"}, {"piste_reponse": "Réponse sûre."}]}
    assert cli._extraire_a_verifier_simulateur(result) == ["[VERIF:citer un arrêt si disponible]"]


def test_extraire_a_verifier_texte_decoupe_par_phrase():
    texte = "Ceci est sûr. Un point [VERIF:référence non trouvée] reste incertain. Ceci aussi est sûr."
    items = cli._extraire_a_verifier_texte(texte)
    assert len(items) == 1
    assert "[VERIF:référence non trouvée]" in items[0]
