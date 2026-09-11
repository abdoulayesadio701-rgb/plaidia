"""
demo.py — Mode démo public de Plaid'IA.

Le mode démo s'active automatiquement si le serveur ne dispose d'aucune clé
API Anthropic par défaut (ni ANTHROPIC_API_KEY, ni apikey.txt), ou si la
variable d'environnement DEMO_MODE=true est positionnée explicitement --
utile pour forcer le mode démo sur un déploiement public même si une clé de
secours traîne, par exemple pour éviter qu'elle ne soit consommée par des
visiteurs. Dans les deux cas, un visiteur qui fournit SA PROPRE clé (en-tête
X-Anthropic-Api-Key, voir le middleware dans main.py) repasse en mode réel
pour ses propres requêtes : le mode démo ne le concerne plus.

Les actions couvertes par des réponses préenregistrées réalistes (voir
demo_data.py) court-circuitent entièrement analyse.py -- aucun appel
Anthropic, aucun coût, disponibles même sans clé du tout. Les actions IA non
couvertes lèvent une 503 explicite via exiger_cle_api() plutôt que de
laisser échouer un appel Anthropic sans clé avec une erreur moins lisible.
"""

import os

import analyse as legacy_analyse
from fastapi import HTTPException

DEMO_MODE_FORCE = os.environ.get("DEMO_MODE", "").strip().lower() in ("1", "true", "yes", "on")

# Réinitialisation destructrice de la base au démarrage (voir main.py::lifespan
# et db.py::reinitialiser_donnees_demo) -- activée PAR DÉFAUT dès que le mode
# démo est actif, pour que la promesse "données non conservées" affichée dans
# l'app soit vraie sur un déploiement public réel. Un développeur qui active
# DEMO_MODE=true en local pour tester le comportement démo SANS perdre sa
# base de travail doit positionner explicitement DEMO_RESET_DB=false --
# faute de quoi la base est vidée et reconstruite à chaque démarrage, y
# compris une base de développement bien remplie. Ne JAMAIS pointer une
# variable DEMO_MODE=true vers une base contenant des données à conserver
# sans avoir d'abord positionné DEMO_RESET_DB=false.
DEMO_RESET_DB = os.environ.get("DEMO_RESET_DB", "true").strip().lower() in ("1", "true", "yes", "on")

# Taille maximale d'un texte libre envoyé par un client (conclusions, notes,
# textes de corpus, questions...) -- protection anti-abus simple demandée en
# plus du débit par IP (voir main.py, slowapi). Configurable au cas où un
# déploiement particulier aurait besoin d'un plafond différent.
MAX_TEXTE_CARACTERES = int(os.environ.get("MAX_TEXTE_CARACTERES", "50000"))


def mode_demo_serveur() -> bool:
    """État structurel du serveur, sans tenir compte d'une éventuelle clé
    personnelle fournie pour la requête en cours -- c'est ce que reflète le
    bandeau "Mode démo" de l'app (GET /api/config), affiché indépendamment
    de ce que fera ensuite tel ou tel visiteur avec sa propre clé.

    Exige à la fois la clé Anthropic (garde-fou, détection d'intention) ET
    la clé DeepSeek (agent principal, vérificateur, critique...) -- depuis
    le changement de fournisseur de modèle, une fonctionnalité réelle a
    besoin des deux pour aboutir ; n'en avoir qu'une ne permettrait qu'un
    garde-fou fonctionnel suivi d'une erreur DeepSeek moins lisible qu'une
    503 de mode démo."""
    return DEMO_MODE_FORCE or not (legacy_analyse.cle_api_configuree() and legacy_analyse.cle_api_deepseek_configuree())


def mode_demo_effectif() -> bool:
    """Mode démo pour la requête HTTP en cours : ignoré si ce visiteur a
    fourni sa propre clé API (voir définir_cle_api_requete, posée par le
    middleware de main.py à partir de l'en-tête X-Anthropic-Api-Key)."""
    if legacy_analyse.obtenir_cle_api_requete():
        return False
    return mode_demo_serveur()


def exiger_cle_api():
    """À appeler en tête d'une route IA non couverte par une réponse
    préenregistrée. Lève une 503 claire plutôt que de laisser _client()
    échouer avec un message moins orienté visiteur."""
    if mode_demo_effectif():
        raise HTTPException(
            status_code=503,
            detail=(
                "Cette fonctionnalité nécessite une clé API Anthropic et n'est pas disponible en mode démo. "
                "Essayez « Analyser des conclusions », « Générer un plan de plaidoirie », "
                "« Simuler les objections », « Chronologie automatique » ou le Chat sur le dossier de "
                "démonstration — ou indiquez votre propre clé via « Utiliser ma propre clé Anthropic » "
                "en pied de page."
            ),
        )
