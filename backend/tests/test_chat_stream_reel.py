"""Chemin RÉEL de /api/chat/stream (hors mode démo, voir test_chemin_reel.py
pour le principe général) -- couvre spécifiquement la détection de
troncature par max_tokens dans analyse.repondre_conversation_stream(),
corrigée le 2026-09-23 (voir son en-tête : avant ce correctif, une réponse
coupée par la limite de tokens envoyait quand même "event: done" comme si
elle était complète, sans la moindre trace)."""

import json

import analyse as legacy_analyse
import pytest
from app import quality_pipeline
from fastapi.testclient import TestClient

CLE = {"x-anthropic-api-key": "sk-ant-test"}


@pytest.fixture(autouse=True)
def sans_appel_modele_annexe(monkeypatch):
    """Neutralise le garde-fou + l'agent d'intention (appelés avant le
    streaming lui-même, voir chat.py::chat_stream) -- seule
    repondre_conversation_stream nous intéresse ici."""
    monkeypatch.setattr(
        quality_pipeline,
        "executer_garde_fou_et_intention",
        lambda message, historique=None: ({}, {"necessite_verification_approfondie": False}),
    )


def _evenements(texte_sse: str) -> list[tuple[str, dict]]:
    evenements = []
    for bloc in texte_sse.split("\n\n"):
        if not bloc.startswith("event:"):
            continue
        entete, _, data_ligne = bloc.partition("\n")
        nom = entete.split("event:", 1)[1].strip()
        data = json.loads(data_ligne.split("data:", 1)[1]) if "data:" in data_ligne else {}
        evenements.append((nom, data))
    return evenements


def test_reponse_tronquee_par_max_tokens_envoie_une_erreur_explicite(monkeypatch, client: TestClient):
    def stream_tronque(messages, contexte_recherche=None):
        yield "Début de la réponse, "
        yield "coupée en plein milieu"
        raise legacy_analyse.ReponseTronqueeError("Réponse de chat tronquée : ...", "Début de la réponse, coupée en plein milieu")

    monkeypatch.setattr(legacy_analyse, "repondre_conversation_stream", stream_tronque)

    r = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "Question longue et complexe"}]},
        headers=CLE,
    )
    assert r.status_code == 200
    evenements = _evenements(r.text)
    noms = [nom for nom, _ in evenements]

    # Les fragments déjà produits avant la troncature restent envoyés --
    # rien n'est perdu côté utilisateur, voir la docstring de chat.py.
    assert noms.count("delta") == 2
    texte_reconstitue = "".join(data["text"] for nom, data in evenements if nom == "delta")
    assert texte_reconstitue == "Début de la réponse, coupée en plein milieu"

    # Une erreur explicite est envoyée -- jamais de "done" après une
    # troncature (avant le correctif : le contraire).
    assert "error" in noms
    assert "done" not in noms
    detail_erreur = next(data["detail"] for nom, data in evenements if nom == "error")
    assert "interrompue" in detail_erreur.lower()
    # Le message affiché à l'utilisateur ne doit pas être le texte brut de
    # l'exception Python (jargon interne), mais un libellé compréhensible.
    assert "ReponseTronqueeError" not in detail_erreur


def test_reponse_complete_hors_demo_envoie_bien_done(monkeypatch, client: TestClient):
    """Non-régression : le chemin normal (pas de troncature) n'est pas cassé
    par le correctif -- toujours "done", jamais "error"."""

    def stream_complet(messages, contexte_recherche=None):
        yield "Réponse "
        yield "complète."

    monkeypatch.setattr(legacy_analyse, "repondre_conversation_stream", stream_complet)

    r = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "Question simple"}]},
        headers=CLE,
    )
    assert r.status_code == 200
    noms = [nom for nom, _ in _evenements(r.text)]
    assert "done" in noms
    assert "error" not in noms
