"""test_usage_log.py — Journal simple d'usage des modèles (chantier
"optimisation des coûts API", tâche 5)."""

import json

import usage_log


def test_journaliser_usage_ecrit_une_ligne_jsonl(tmp_path, monkeypatch):
    fichier = tmp_path / "sous_dossier" / "usage_api.jsonl"
    monkeypatch.setattr(usage_log, "LOG_FILE", fichier)

    usage_log.journaliser_usage("deepseek", "extraction", "deepseek-ai/deepseek-v4-pro-0813", 100, 20)
    usage_log.journaliser_usage("claude", "analyse", "claude-sonnet-4-6", 500, 300)

    lignes = fichier.read_text(encoding="utf-8").strip().splitlines()
    assert len(lignes) == 2

    premiere = json.loads(lignes[0])
    assert premiere["fournisseur"] == "deepseek"
    assert premiere["tache"] == "extraction"
    assert premiere["tokens_entree"] == 100
    assert premiere["tokens_sortie"] == 20
    assert "horodatage" in premiere


def test_journaliser_usage_ne_leve_jamais_meme_si_lecriture_echoue(monkeypatch):
    """Une panne d'écriture du log ne doit jamais faire remonter une
    exception -- elle ne doit jamais faire échouer l'appel API réel."""
    class _CheminImpossible:
        parent = type("P", (), {"mkdir": staticmethod(lambda **k: (_ for _ in ()).throw(OSError("disque plein")))})()

    monkeypatch.setattr(usage_log, "LOG_FILE", _CheminImpossible())
    usage_log.journaliser_usage("deepseek", "extraction", "m", 1, 1)  # ne lève rien
