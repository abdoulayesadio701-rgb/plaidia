"""Une clé API collée avec un espace ou un retour à la ligne invisible doit
fonctionner : le SDK Anthropic répond sinon "Connection error." (et non une
erreur d'authentification), ce qui a bloqué le chat en production le
2026-09-25. Voir analyse._client()."""

import analyse
import pytest


@pytest.mark.parametrize("brut", ["sk-ant-api03-abc", "sk-ant-api03-abc\n", " sk-ant-api03-abc ", "sk-ant-api03-abc\r\n", "\tsk-ant-api03-abc\n "])
def test_client_ignore_les_espaces_autour_de_la_cle_d_environnement(monkeypatch, brut):
    monkeypatch.setenv("ANTHROPIC_API_KEY", brut)
    assert analyse._client().api_key == "sk-ant-api03-abc"


def test_client_ignore_les_espaces_autour_de_la_cle_de_requete(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    jeton = analyse.definir_cle_api_requete("  sk-ant-api03-perso\n")
    try:
        assert analyse._client().api_key == "sk-ant-api03-perso"
    finally:
        analyse.reinitialiser_cle_api_requete(jeton)


def test_une_cle_faite_uniquement_d_espaces_est_consideree_absente(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "  \n")
    monkeypatch.setattr(analyse, "KEY_FILE", tmp_path / "absent.txt")
    with pytest.raises(EnvironmentError):
        analyse._client()


def test_la_cle_nvidia_est_nettoyee_aussi(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-xyz\n")
    assert analyse._cle_api_nvidia() == "nvapi-xyz"
