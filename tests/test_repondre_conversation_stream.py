"""test_repondre_conversation_stream.py — Détection de troncature par
max_tokens dans analyse.repondre_conversation_stream(), corrigée le
2026-09-23 (voir l'en-tête de la fonction) : avant ce correctif, une
réponse coupée par la limite de tokens s'arrêtait juste de produire, sans
qu'aucune exception ne soit levée -- exactement le bug diagnostiqué sur le
chat (réponse tronquée en plein milieu, sans le moindre message d'erreur).

Ici, on mocke directement analyse._client() (jamais de vrai appel réseau) --
voir backend/tests/test_chat_stream_reel.py pour la couverture côté routeur
FastAPI (event SSE "error" envoyé au front)."""

from types import SimpleNamespace

import analyse


class _StreamSimule:
    """Reproduit juste assez de l'API `with client.messages.stream(...) as
    stream:` du SDK Anthropic (contexte + .text_stream + .get_final_message())
    pour tester repondre_conversation_stream() sans réseau."""

    def __init__(self, fragments: list[str], stop_reason: str, texte_final: str):
        self._fragments = fragments
        self._stop_reason = stop_reason
        self._texte_final = texte_final

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def text_stream(self):
        return iter(self._fragments)

    def get_final_message(self):
        return SimpleNamespace(
            stop_reason=self._stop_reason,
            usage=SimpleNamespace(input_tokens=123, output_tokens=456),
            content=[SimpleNamespace(type="text", text=self._texte_final)],
        )


def _client_simule(stream):
    return SimpleNamespace(messages=SimpleNamespace(stream=lambda **kwargs: stream))


def test_reponse_complete_ne_leve_rien(monkeypatch):
    stream = _StreamSimule(["Bonjour, ", "voici la réponse complète."], stop_reason="end_turn", texte_final="Bonjour, voici la réponse complète.")
    monkeypatch.setattr(analyse, "_client", lambda: _client_simule(stream))

    fragments = list(analyse.repondre_conversation_stream([{"role": "user", "content": "Question"}]))
    assert fragments == ["Bonjour, ", "voici la réponse complète."]


def test_reponse_tronquee_par_max_tokens_leve_reponse_tronquee_error(monkeypatch):
    stream = _StreamSimule(["Début ", "coupé"], stop_reason="max_tokens", texte_final="Début coupé")
    monkeypatch.setattr(analyse, "_client", lambda: _client_simule(stream))

    generateur = analyse.repondre_conversation_stream([{"role": "user", "content": "Question longue"}])
    # Les fragments déjà produits avant la troncature restent bien
    # accessibles à l'appelant (voir chat.py::event_stream, qui les a déjà
    # envoyés en "delta" avant que l'exception ne se déclenche) -- seule la
    # toute dernière itération lève.
    fragments_recus = []
    leve = None
    try:
        for fragment in generateur:
            fragments_recus.append(fragment)
    except analyse.ReponseTronqueeError as e:
        leve = e

    assert fragments_recus == ["Début ", "coupé"]
    assert leve is not None
    assert leve.raw == "Début coupé"
    assert "max_tokens" in str(leve) or "tokens" in str(leve).lower()
