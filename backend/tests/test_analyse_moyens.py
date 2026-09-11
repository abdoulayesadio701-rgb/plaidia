"""
test_analyse_moyens.py — Chantier "temps de traitement des générations",
§2e : découpe des conclusions adverses en moyens et analyse parallèle.

Portée : la découpe heuristique et l'orchestration (séquentiel si un seul
moyen, parallèle sinon, fusion triée par risque) sont testées directement,
sans réseau -- analyser_conclusions() (l'appel LLM réel par moyen) est
mocké, comme le reste des agents de analyse.py dans cette suite (voir
test_quality_pipeline.py)."""

import time

import analyse as legacy_analyse


# --- Découpe heuristique -----------------------------------------------------

def test_texte_sans_marqueur_reste_un_seul_moyen():
    texte = "Les conclusions adverses soutiennent que le contrat est nul. Sur ce point, la jurisprudence est constante."
    assert legacy_analyse._decouper_conclusions_en_moyens(texte) == [texte]


def test_decoupe_sur_premier_et_second_moyen():
    texte = (
        "Exposé des faits : les parties ont conclu un contrat en 2020.\n\n"
        "PREMIER MOYEN : le contrat est nul pour vice du consentement. Développement détaillé du premier moyen sur plusieurs lignes.\n\n"
        "SECOND MOYEN : subsidiairement, le préjudice n'est pas démontré. Développement détaillé du second moyen également étoffé."
    )
    moyens = legacy_analyse._decouper_conclusions_en_moyens(texte)
    assert len(moyens) == 2
    assert moyens[0].startswith("Exposé des faits") and "PREMIER MOYEN" in moyens[0]
    assert moyens[1].startswith("SECOND MOYEN")


def test_decoupe_sur_numerotation_romaine():
    texte = (
        "I. Sur la recevabilité de la demande, plusieurs arguments doivent être développés avec un minimum de substance.\n\n"
        "II. Sur le fond du litige, la partie adverse invoque une créance qui n'est étayée par aucune pièce probante."
    )
    moyens = legacy_analyse._decouper_conclusions_en_moyens(texte)
    assert len(moyens) == 2


def test_fragment_trop_court_est_rattache_au_precedent():
    """Un marqueur suivi d'un fragment trop court pour être un moyen
    exploitable seul (ex. un simple renvoi) est rattaché au moyen précédent
    plutôt que traité comme un moyen à part -- évite un sur-découpage."""
    texte = (
        "PREMIER MOYEN : argumentation complète et développée sur plusieurs lignes concernant la nullité du contrat invoquée.\n\n"
        "SECOND MOYEN : voir plus haut."
    )
    moyens = legacy_analyse._decouper_conclusions_en_moyens(texte)
    assert len(moyens) == 1
    assert "SECOND MOYEN" in moyens[0]


# --- Orchestration : séquentiel si un seul moyen, parallèle sinon -----------

def test_analyser_conclusions_par_moyens_reste_sequentiel_si_un_seul_moyen(monkeypatch):
    appels = []

    def _espion(texte, *a, **k):
        appels.append(texte)
        return {"arguments": [{"resume": "a", "risque": "Moyen"}], "points_attention": []}

    monkeypatch.setattr(legacy_analyse, "analyser_conclusions", _espion)
    texte = "Un texte de conclusions sans aucun marqueur de moyen détectable."
    resultat = legacy_analyse.analyser_conclusions_par_moyens(texte)
    assert appels == [texte]  # un seul appel, sur le texte entier -- comportement inchangé
    assert resultat["arguments"][0]["resume"] == "a"


def test_analyser_conclusions_par_moyens_lance_un_appel_parallele_par_moyen(monkeypatch):
    appels = []

    def _espion_lent(texte, *a, **k):
        appels.append(texte)
        time.sleep(0.15)
        risque = "Élevé" if "PREMIER" in texte else "Faible"
        return {"arguments": [{"resume": texte[:20], "risque": risque}], "points_attention": [f"point de {texte[:10]}"]}

    monkeypatch.setattr(legacy_analyse, "analyser_conclusions", _espion_lent)
    monkeypatch.setattr(legacy_analyse, "_verifier_coherence_globale_moyens", lambda arguments: "")

    texte = (
        "PREMIER MOYEN : argumentation développée sur plusieurs lignes concernant la nullité du contrat invoquée ici.\n\n"
        "SECOND MOYEN : argumentation développée sur plusieurs lignes concernant le quantum du préjudice réclamé ici."
    )
    t0 = time.monotonic()
    resultat = legacy_analyse.analyser_conclusions_par_moyens(texte)
    duree = time.monotonic() - t0

    assert len(appels) == 2  # un appel par moyen détecté
    assert duree < 0.28  # bien moins que 0.3s (0.15 + 0.15 séquentiel) -- preuve de la parallélisation
    # Les arguments fusionnés sont triés du risque le plus élevé au plus faible.
    assert [a["risque"] for a in resultat["arguments"]] == ["Élevé", "Faible"]
    assert len(resultat["points_attention"]) == 2


def test_note_de_coherence_globale_ajoutee_si_non_vide(monkeypatch):
    monkeypatch.setattr(
        legacy_analyse, "analyser_conclusions",
        lambda texte, *a, **k: {"arguments": [{"resume": "a", "risque": "Moyen"}], "points_attention": []},
    )
    monkeypatch.setattr(legacy_analyse, "_verifier_coherence_globale_moyens", lambda arguments: "Contradiction relevée entre les deux moyens.")
    texte = "PREMIER MOYEN : un moyen suffisamment développé pour être détecté comme tel par le découpage heuristique.\n\nSECOND MOYEN : un autre moyen suffisamment développé pour être détecté lui aussi par ce même découpage."
    resultat = legacy_analyse.analyser_conclusions_par_moyens(texte)
    assert "Contradiction relevée entre les deux moyens." in resultat["points_attention"]


# --- §2c : modèle plus léger pour les étapes de classification -------------

def test_modele_leger_distinct_du_modele_lourd():
    """MODEL_LEGER (Claude, étapes de classification) et MODEL_LOURD
    (DeepSeek, agent principal/vérificateur/critique/stratégie combative)
    restent deux fournisseurs distincts -- voir la demande explicite de
    changement de fournisseur de modèle."""
    assert legacy_analyse.MODEL_LEGER != legacy_analyse.MODEL_LOURD


def test_garde_fou_et_intention_utilisent_le_modele_leger(monkeypatch):
    """Vérifie que le modèle réellement transmis à l'API pour les étapes de
    classification (§2c) est MODEL_LEGER, pas MODEL_ACTIF -- sans appel
    réseau (client Anthropic mocké)."""
    modeles_utilises = []

    class _ReponseFactice:
        class _Bloc:
            text = '{"allowed": true, "risk_level": "low", "reason": "", "requires_clarification": false}'
        content = [_Bloc()]

    class _ClientFactice:
        class messages:
            @staticmethod
            def create(model, **kwargs):
                modeles_utilises.append(model)
                return _ReponseFactice()

    monkeypatch.setattr(legacy_analyse, "_client", lambda: _ClientFactice())
    legacy_analyse.evaluer_garde_fou_entree("Un texte suffisamment long pour déclencher un vrai appel au modèle de garde-fou.")
    assert modeles_utilises == [legacy_analyse.MODEL_LEGER]
