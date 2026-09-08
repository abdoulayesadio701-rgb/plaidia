"""
security_guard.py — Garde-fou d'entrée (SÉCURITÉ), voir
ARCHITECTURE_MULTI_AGENTS.md §1 et §8.

Séparation stricte sécurité / qualité demandée par la consigne : ce module
ne contient AUCUNE logique de vérification de contenu juridique (citations,
raisonnement, cohérence) -- seulement le filtrage d'entrée d'une demande
avant qu'elle n'atteigne un agent d'analyse. La couche qualité (vérificateur
juridique, contradicteur, validateur final) vit exclusivement dans
quality_pipeline.py et ne dépend jamais de ce module.

Le prompt système et l'appel Claude eux-mêmes vivent dans analyse.py
(analyse.evaluer_garde_fou_entree), exactement comme toute autre fonction
d'analyse -- ce module n'ajoute que l'exception typée et le point d'entrée
unique utilisé par les routers.
"""

import analyse as legacy_analyse


class DemandeRefusee(Exception):
    """Levée quand le garde-fou d'entrée juge une demande non recevable
    (allowed=False). Gérée dans main.py comme les autres exceptions métier
    (voir la section "Gestion d'erreurs uniforme") -- jamais une trace
    Python brute renvoyée au front."""

    def __init__(self, reason: str, risk_level: str = "medium"):
        super().__init__(reason)
        self.reason = reason
        self.risk_level = risk_level


def executer_garde_fou(texte: str) -> dict:
    """Point d'entrée unique du garde-fou pour les routers : évalue `texte`
    et lève DemandeRefusee si la demande n'est pas recevable (allowed=False).
    Retourne l'évaluation complète sinon -- c'est à l'appelant de décider
    quoi faire de requires_clarification=True selon le contexte de la
    fonctionnalité (l'endpoint n'est pas bloqué pour autant, ce n'est qu'une
    indication)."""
    evaluation = legacy_analyse.evaluer_garde_fou_entree(texte)
    if not evaluation.get("allowed", True):
        raise DemandeRefusee(
            evaluation.get("reason") or "Cette demande ne peut pas être traitée.",
            evaluation.get("risk_level", "medium"),
        )
    return evaluation
