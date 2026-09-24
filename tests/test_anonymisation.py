"""
test_anonymisation.py — Détection locale de noms de personnes et
pseudonymisation réversible (anonymisation.py), voir sa docstring de module
pour le périmètre et les limites de l'heuristique. Aucun appel réseau."""

import anonymisation as anon


def test_texte_sans_nom_n_est_pas_modifie():
    texte = "Le contrat a été résilié le 3 janvier 2024 pour manquement contractuel."
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert anonymise == texte
    assert mapping == {}


def test_texte_vide():
    assert anon.anonymiser_texte("") == ("", {})


def test_detection_par_civilite():
    texte = "M. Diallo conteste la décision. Maître Dupont représente la défenderesse."
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert "Diallo" not in anonymise
    assert "Dupont" not in anonymise
    assert "M. Personne A conteste" in anonymise
    assert "Maître Personne B représente" in anonymise
    assert set(mapping.values()) == {"Diallo", "Dupont"}


def test_detection_prenom_nom_majuscules():
    texte = "Le contrat a été signé par Amadou DIALLO le 3 janvier 2024, en présence de Fatou KEITA."
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert "DIALLO" not in anonymise and "KEITA" not in anonymise
    assert "Personne A" in anonymise and "Personne B" in anonymise
    assert mapping == {"Personne A": "Amadou DIALLO", "Personne B": "Fatou KEITA"}


def test_detection_prenom_du_repertoire_plus_nom_capitalise():
    texte = "Jean Dupont a signé le contrat au nom de la société Atlas Logistique."
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert "Jean Dupont" not in anonymise
    assert list(mapping.values()) == ["Jean Dupont"]
    # "Atlas Logistique" (nom de société, pas dans le répertoire des prénoms) n'est pas touché.
    assert "Atlas Logistique" in anonymise


def test_deux_mots_capitalises_hors_repertoire_ne_sont_pas_captures_a_tort():
    # Ni "Cour" ni "Cassation" ne sont des prénoms connus -- pas de faux positif.
    texte = "La Cour Cassation a rendu son arrêt le 3 janvier 2024."
    anonymise, _mapping = anon.anonymiser_texte(texte)
    assert anonymise == texte


def test_meme_personne_mentionnee_plusieurs_fois_recoit_le_meme_pseudonyme():
    texte = "M. Diallo a signé le contrat. Plus tard, M. Diallo a été mis en demeure."
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert anonymise.count("Personne A") == 2
    assert len(mapping) == 1


def test_nom_complet_puis_seul_nom_de_famille_partagent_le_pseudonyme():
    texte = "M. Amadou Diallo conteste la décision. M. Diallo affirme ne rien devoir."
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert anonymise.count("Personne A") == 2
    assert mapping == {"Personne A": "Amadou Diallo"}  # la forme la plus complète est restituée


def test_plusieurs_personnes_distinctes_recoivent_des_pseudonymes_differents():
    texte = "M. Diallo (demandeur) s'oppose à Mme Traoré (défenderesse)."
    _anonymise, mapping = anon.anonymiser_texte(texte)
    assert len(mapping) == 2
    assert set(mapping.values()) == {"Diallo", "Traoré"}


def test_plus_de_26_personnes_genere_des_pseudonymes_a_deux_lettres():
    noms = [f"M. Nom{n}" for n in range(30)]
    texte = " ".join(noms)
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert len(mapping) == 30
    assert "Personne A" in anonymise and "Personne AA" in anonymise


def test_deanonymiser_restitue_le_texte_original():
    texte = "M. Diallo conteste la décision rendue contre lui."
    anonymise, mapping = anon.anonymiser_texte(texte)
    assert anon.deanonymiser(anonymise, mapping) == texte


def test_deanonymiser_parcourt_recursivement_dict_et_liste():
    mapping = {"Personne A": "Amadou Diallo"}
    structure = {
        "arguments": [{"resume": "Personne A n'a pas respecté ses obligations.", "risque": "Élevé"}],
        "points_attention": ["Vérifier le domicile de Personne A."],
        "note": 3,
    }
    resultat = anon.deanonymiser(structure, mapping)
    assert resultat["arguments"][0]["resume"] == "Amadou Diallo n'a pas respecté ses obligations."
    assert resultat["points_attention"][0] == "Vérifier le domicile de Amadou Diallo."
    assert resultat["note"] == 3  # types non textuels inchangés


def test_deanonymiser_sans_mapping_ne_modifie_rien():
    assert anon.deanonymiser("Texte quelconque", {}) == "Texte quelconque"
    structure = {"a": ["x", "y"]}
    assert anon.deanonymiser(structure, {}) == structure
