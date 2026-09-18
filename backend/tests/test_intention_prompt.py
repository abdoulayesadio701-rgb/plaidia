"""Le prompt du routeur d'intention doit connaître toutes les actions que la
barre de commande sait ouvrir (frontend/src/config/intentions.ts)."""

import analyse as legacy_analyse

ACTIONS_NAVIGABLES = [
    "importer", "analyser", "resumer", "plan", "simulateur", "rapport", "note",
    "notes_consulter", "note_client", "chronologie", "verification", "delais",
    "entrainement", "bordereau",
]


def test_le_prompt_declare_chaque_action_navigable():
    for action in ACTIONS_NAVIGABLES:
        assert f'- "{action}" :' in legacy_analyse.INTENTION_SYSTEM_PROMPT, action
