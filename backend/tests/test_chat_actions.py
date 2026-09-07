"""
test_chat_actions.py — Tests de la couche de validation entre le LLM et
l'état applicatif (voir app/chat_actions.py et
ARCHITECTURE_CHAT_CONTEXTUEL.md §2.4). Logique pure, aucun appel réseau ni
base de données : ce que le modèle pourrait proposer de mal formé ne doit
jamais atteindre l'état réel de l'application.
"""

import pytest

from app import chat_actions


@pytest.fixture()
def resultat():
    return {
        "arguments": [
            {"resume": "Premier argument", "refutations": [{"angle": "Factuel", "piste": "Piste A"}]},
            {"resume": "Deuxième argument", "refutations": []},
        ],
        "points_attention": ["Un point"],
        "accroche": "Texte d'accroche",
        "analyse_id": None,
    }


class TestValiderAction:
    def test_scope_global_toujours_valide(self, resultat):
        chat_actions.valider_action("conclusions", "global", "rewrite", resultat)  # ne lève pas

    def test_scope_indexe_valide(self, resultat):
        chat_actions.valider_action("conclusions", "arguments[1]", "rewrite", resultat)

    def test_scope_scalaire_valide(self, resultat):
        chat_actions.valider_action("conclusions", "accroche", "rewrite", resultat)

    def test_index_hors_limites_rejete(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "arguments[5]", "rewrite", resultat)

    def test_index_negatif_rejete(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "arguments[-1]", "rewrite", resultat)

    def test_champ_inexistant_rejete(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "champ_invente", "rewrite", resultat)

    def test_operation_inconnue_rejetee(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "global", "operation_inventee", resultat)

    def test_liste_sans_index_rejetee_sauf_pour_add(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "arguments", "rewrite", resultat)
        chat_actions.valider_action("conclusions", "arguments", "add", resultat)  # ne lève pas

    def test_scope_imbrique_valide(self, resultat):
        """Cas réel rencontré en test manuel : le modèle cible directement
        la sous-liste des réfutations d'un argument précis plutôt que
        l'argument entier -- doit être accepté, pas seulement "arguments[i]"."""
        chat_actions.valider_action("conclusions", "arguments[0].refutations", "add", resultat)
        chat_actions.valider_action("conclusions", "arguments[0].refutations[0]", "rewrite", resultat)
        chat_actions.valider_action("conclusions", "arguments[0].refutations[0]", "delete", resultat)

    def test_scope_imbrique_index_hors_limites_rejete(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "arguments[0].refutations[9]", "rewrite", resultat)

    def test_scope_imbrique_champ_inexistant_rejete(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "arguments[0].champ_invente", "rewrite", resultat)

    def test_scope_imbrique_index_parent_hors_limites_rejete(self, resultat):
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("conclusions", "arguments[9].refutations", "add", resultat)

    def test_champ_complexe_refuse_scope_precis(self):
        """Un champ dont la valeur n'est ni une chaîne ni une liste (ex. un
        dict imbriqué comme elements_par_document de CoherenceOut) ne peut
        être visé que via scope="global" -- jamais réécrit à l'aveugle."""
        resultat_coherence = {"elements_par_document": {"doc1": {"dates": []}}, "contradictions": []}
        with pytest.raises(chat_actions.ActionInvalide):
            chat_actions.valider_action("coherence", "elements_par_document", "rewrite", resultat_coherence)


class TestAppliquerPatch:
    def test_patch_local_ne_modifie_pas_les_autres_elements(self, resultat):
        patch = chat_actions.appliquer_patch(resultat, "arguments[1]", "rewrite", {"resume": "Modifié"})
        assert patch["arguments"][0]["resume"] == "Premier argument"  # intact
        assert patch["arguments"][1]["resume"] == "Modifié"
        assert patch["accroche"] == "Texte d'accroche"  # intact
        assert patch["points_attention"] == ["Un point"]  # intact

    def test_original_jamais_mute(self, resultat):
        chat_actions.appliquer_patch(resultat, "arguments[0]", "rewrite", {"resume": "Modifié"})
        assert resultat["arguments"][0]["resume"] == "Premier argument"

    def test_ajout_en_fin_de_liste(self, resultat):
        patch = chat_actions.appliquer_patch(resultat, "arguments", "add", {"resume": "Nouveau"})
        assert len(patch["arguments"]) == 3
        assert patch["arguments"][2]["resume"] == "Nouveau"
        assert len(resultat["arguments"]) == 2  # original intact

    def test_suppression_d_un_element(self, resultat):
        patch = chat_actions.appliquer_patch(resultat, "arguments[0]", "delete", None)
        assert len(patch["arguments"]) == 1
        assert patch["arguments"][0]["resume"] == "Deuxième argument"

    def test_reecriture_champ_scalaire(self, resultat):
        patch = chat_actions.appliquer_patch(resultat, "accroche", "rewrite", "Nouvelle accroche")
        assert patch["accroche"] == "Nouvelle accroche"
        assert patch["arguments"] == resultat["arguments"]  # intact

    def test_mise_a_jour_globale_remplace_tout(self, resultat):
        nouveau = {"arguments": [], "points_attention": [], "accroche": "", "analyse_id": None}
        patch = chat_actions.appliquer_patch(resultat, "global", "rewrite", nouveau)
        assert patch == nouveau

    def test_ajout_imbrique_ne_touche_que_l_argument_cible(self, resultat):
        """Cas réel : « ajoute une réfutation à cet argument » -- seul
        arguments[0].refutations grandit, arguments[1] reste inchangé."""
        patch = chat_actions.appliquer_patch(
            resultat, "arguments[0].refutations", "add", {"angle": "Juridique", "piste": "Nouvelle piste"}
        )
        assert len(patch["arguments"][0]["refutations"]) == 2
        assert patch["arguments"][0]["refutations"][1]["piste"] == "Nouvelle piste"
        assert patch["arguments"][0]["refutations"][0]["piste"] == "Piste A"  # intact
        assert patch["arguments"][1] == resultat["arguments"][1]  # intact
        assert len(resultat["arguments"][0]["refutations"]) == 1  # original non muté

    def test_suppression_imbriquee(self, resultat):
        patch = chat_actions.appliquer_patch(resultat, "arguments[0].refutations[0]", "delete", None)
        assert patch["arguments"][0]["refutations"] == []
        assert len(resultat["arguments"][0]["refutations"]) == 1  # original non muté

    def test_reecriture_imbriquee(self, resultat):
        patch = chat_actions.appliquer_patch(
            resultat, "arguments[0].refutations[0]", "rewrite", {"angle": "Factuel", "piste": "Piste réécrite"}
        )
        assert patch["arguments"][0]["refutations"][0]["piste"] == "Piste réécrite"
        assert patch["arguments"][1]["resume"] == "Deuxième argument"  # intact
