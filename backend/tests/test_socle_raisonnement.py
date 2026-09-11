"""
test_socle_raisonnement.py — analyse.REGLE_SOCLE_RAISONNEMENT.

Discipline de construction d'un argument (texte de loi > jurisprudence
constante > hiérarchie des normes > faits qualifiés > précédents >
analogie/distinction > force de la motivation), sur demande explicite de
l'utilisateur. Portée volontairement limitée aux prompts qui construisent
littéralement un argument destiné à une plaidoirie (voir le commentaire
au-dessus de la constante dans analyse.py) -- pas aux prompts de
structuration/consultation, décision confirmée avec l'utilisateur avant
implémentation.
"""

import analyse as legacy_analyse

_PROMPTS_COUVERTS = [
    "SYSTEM_PROMPT",
    "PARAGRAPHE_SYSTEM_PROMPT",
    "PLAN_SYSTEM_PROMPT",
    "STRATEGIE_COMBATIVE_SYSTEM_PROMPT",
]

_PROMPTS_NON_COUVERTS = [
    "QUESTION_SYSTEM_PROMPT",
    "SIMULATEUR_SYSTEM_PROMPT",
    "CHRONOLOGIE_SYSTEM_PROMPT",
    "EXTRACTION_SYSTEM_PROMPT",
    "CLASSEMENT_SYSTEM_PROMPT",
    "PV_SYSTEM_PROMPT",
    "REQUISITOIRE_SYSTEM_PROMPT",
    "RAPPORT_INSTRUCTION_SYSTEM_PROMPT",
    "COHERENCE_MOYENS_SYSTEM_PROMPT",
    "EDITION_SYSTEM_PROMPT",
    "VERIFICATION_PROCEDURALE_SYSTEM_PROMPT",
    "POSITION_JURISPRUDENCE_SYSTEM_PROMPT",
    "JURISPRUDENCE_CONSULT_SYSTEM_PROMPT",
    "TRADUCTION_SYSTEM_PROMPT",
]


def test_les_prompts_de_construction_dargument_contiennent_le_socle():
    for nom in _PROMPTS_COUVERTS:
        prompt = getattr(legacy_analyse, nom)
        assert legacy_analyse.REGLE_SOCLE_RAISONNEMENT in prompt, f"{nom} devrait contenir REGLE_SOCLE_RAISONNEMENT"


def test_le_socle_precede_le_balisage_des_citations():
    """Règle de fond (comment raisonner) avant règle de forme (comment
    citer) -- voir le commentaire au-dessus de la constante."""
    for nom in _PROMPTS_COUVERTS:
        prompt = getattr(legacy_analyse, nom)
        assert prompt.index(legacy_analyse.REGLE_SOCLE_RAISONNEMENT) < prompt.index(legacy_analyse.REGLE_BALISAGE_CITATIONS)


def test_les_autres_prompts_juridiques_ne_contiennent_pas_le_socle():
    """Portée volontairement limitée -- confirmée avec l'utilisateur avant
    implémentation (AskUserQuestion) : les prompts de structuration/
    consultation ne construisent pas d'argument, ils n'ont pas à recevoir
    cette discipline de raisonnement."""
    for nom in _PROMPTS_NON_COUVERTS:
        prompt = getattr(legacy_analyse, nom)
        assert legacy_analyse.REGLE_SOCLE_RAISONNEMENT not in prompt, f"{nom} ne devrait pas contenir REGLE_SOCLE_RAISONNEMENT"


def test_le_contenu_du_socle_liste_bien_les_sept_criteres_dans_lordre():
    texte = legacy_analyse.REGLE_SOCLE_RAISONNEMENT
    criteres = [
        "Texte de loi applicable",
        "Jurisprudence constante",
        "Hiérarchie des normes",
        "Faits du dossier qualifiés juridiquement",
        "Précédents favorables",
        "Raisonnement par analogie",
        "Force de la motivation",
    ]
    positions = [texte.index(c) for c in criteres]
    assert positions == sorted(positions)
