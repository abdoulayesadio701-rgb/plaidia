"""
test_anonymisation_router.py — Option "Anonymiser les noms avant l'envoi"
(ConclusionsIn.anonymiser, voir anonymisation.py) sur POST /api/analyse/
conclusions et sa variante /stream : vérifie que le vrai nom d'une personne
mentionnée dans le texte des conclusions ne part JAMAIS vers les fonctions
qui appellent un modèle (garde-fou, agent principal, vérificateur, critique)
quand l'option est activée, et que le résultat renvoyé/enregistré affiche
bien le vrai nom (dépseudonymisation).

Mode démo contourné via X-Anthropic-Api-Key, comme test_chat_contextuel.py --
toutes les fonctions qui appelleraient réellement Claude sont monkeypatchées,
aucun appel réseau dans cette suite."""

import json

import analyse as legacy_analyse
import db
import pytest
from fastapi.testclient import TestClient

_HEADERS_CLE_TEST = {"x-anthropic-api-key": "sk-ant-cle-de-test"}
_TEXTE_AVEC_NOM = "M. Diallo conteste les faits qui lui sont reprochés et affirme avoir respecté ses obligations."


def _evenements_sse(texte: str) -> dict[str, dict]:
    evenements = {}
    for bloc in texte.split("\n\n"):
        if bloc.startswith("event: "):
            nom, _, reste = bloc.partition("\n")
            nom = nom.removeprefix("event: ")
            evenements[nom.removeprefix("event: ")] = json.loads(reste.split("data:", 1)[1])
    return evenements


@pytest.fixture()
def _agents_captures(monkeypatch):
    """Monkeypatch les 4 points d'entrée qui appelleraient réellement un
    modèle pour cette fonctionnalité (garde-fou, agent principal,
    vérificateur, critique) : chacun capture le texte qu'il a reçu, et
    répond en le recopiant dans le résultat -- ce qui permet de vérifier
    après coup si c'est le vrai nom ou un pseudonyme qui a été envoyé."""
    recu: dict[str, str] = {}

    def _garde_fou(texte):
        recu["garde_fou"] = texte
        return {"allowed": True, "risk_level": "low", "reason": "", "requires_clarification": False}

    def _agent_principal(texte):
        recu["agent_principal"] = texte
        return {
            "arguments": [{"resume": f"Analyse portant sur : {texte}", "fondement": "", "risque": "?", "justification_risque": "", "refutations": []}],
            "points_attention": [f"Point de vigilance concernant : {texte}"],
        }

    def _verificateur(contenu_a_verifier, citations_evaluees, contexte_sources=""):
        recu["verificateur"] = contenu_a_verifier
        return {"statut_global": "VERIFIE", "elements": []}

    def _critique(contenu_a_critiquer, contexte_dossier=""):
        recu["critique"] = contenu_a_critiquer
        return {"critiques": [], "synthese": ""}

    monkeypatch.setattr(legacy_analyse, "evaluer_garde_fou_entree", _garde_fou)
    monkeypatch.setattr(legacy_analyse, "analyser_conclusions_par_moyens", _agent_principal)
    monkeypatch.setattr(legacy_analyse, "verifier_juridiquement", _verificateur)
    monkeypatch.setattr(legacy_analyse, "critiquer_reponse", _critique)
    return recu


def test_sans_anonymisation_le_vrai_nom_part_tel_quel(client: TestClient, _agents_captures):
    r = client.post(
        "/api/analyse/conclusions",
        json={"texte": _TEXTE_AVEC_NOM, "anonymiser": False},
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    assert "Diallo" in _agents_captures["garde_fou"]
    assert "Diallo" in _agents_captures["agent_principal"]
    assert "Diallo" in _agents_captures["verificateur"]
    assert "Diallo" in r.json()["arguments"][0]["resume"]


def test_anonymisation_masque_le_nom_envoye_et_le_restitue_dans_la_reponse(client: TestClient, _agents_captures):
    r = client.post(
        "/api/analyse/conclusions",
        json={"texte": _TEXTE_AVEC_NOM, "anonymiser": True},
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    data = r.json()

    # Le vrai nom n'a jamais atteint aucune des 4 fonctions qui appellent un modèle.
    for etape, texte_recu in _agents_captures.items():
        assert "Diallo" not in texte_recu, f"le vrai nom a fuité vers {etape}"
        assert "Personne A" in texte_recu, f"aucun pseudonyme envoyé à {etape}"

    # La réponse renvoyée au front, elle, affiche le vrai nom.
    assert "Diallo" in data["arguments"][0]["resume"]
    assert "Personne A" not in data["arguments"][0]["resume"]
    assert "Diallo" in data["points_attention"][0]


def test_anonymisation_sauvegarde_le_vrai_nom_dans_le_dossier(client: TestClient, _agents_captures, dossier_demo_id: int):
    """Le dossier de l'avocat doit garder les vrais noms -- l'anonymisation
    ne concerne que ce qui part vers le modèle, jamais ce qui est persisté."""
    r = client.post(
        "/api/analyse/conclusions",
        json={"texte": _TEXTE_AVEC_NOM, "anonymiser": True, "dossier_id": dossier_demo_id},
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    analyse_id = r.json()["analyse_id"]
    assert analyse_id is not None
    enregistre = json.loads(db.get_analyse(analyse_id)["arguments_json"])
    assert "Diallo" in enregistre[0]["resume"]
    assert "Personne A" not in json.dumps(enregistre, ensure_ascii=False)


def test_anonymisation_sur_le_flux_stream(client: TestClient, _agents_captures):
    r = client.post(
        "/api/analyse/conclusions/stream",
        json={"texte": _TEXTE_AVEC_NOM, "anonymiser": True},
        headers=_HEADERS_CLE_TEST,
    )
    assert r.status_code == 200
    for etape, texte_recu in _agents_captures.items():
        assert "Diallo" not in texte_recu, f"le vrai nom a fuité vers {etape}"

    evenements = _evenements_sse(r.text)
    assert "Diallo" in evenements["principal"]["arguments"][0]["resume"]
    assert "Personne A" not in evenements["principal"]["arguments"][0]["resume"]


def test_texte_sans_nom_detecte_n_est_pas_modifie(client: TestClient, _agents_captures):
    """Aucun faux positif à masquer : le texte part inchangé, et le
    résultat aussi -- l'option ne doit rien casser sur du texte ordinaire."""
    texte = "Le contrat a été résilié le 3 janvier 2024 pour manquement contractuel."
    r = client.post("/api/analyse/conclusions", json={"texte": texte, "anonymiser": True}, headers=_HEADERS_CLE_TEST)
    assert r.status_code == 200
    assert _agents_captures["agent_principal"] == texte
    assert texte in r.json()["arguments"][0]["resume"]


def test_anonymiser_absent_du_payload_ne_casse_rien_et_vaut_faux(client: TestClient, _agents_captures):
    r = client.post("/api/analyse/conclusions", json={"texte": _TEXTE_AVEC_NOM}, headers=_HEADERS_CLE_TEST)
    assert r.status_code == 200
    assert "Diallo" in _agents_captures["agent_principal"]
