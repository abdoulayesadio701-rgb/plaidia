#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/conftest.py — Configuration partagée pour pytest
"""

import pytest
import sys
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def project_root():
    """Retourne le chemin du dossier racine du projet."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_text():
    """Texte d'exemple pour les tests."""
    return """
    Les conclusions adverses contestent notre position sur plusieurs points :
    
    1. Violation du contrat de travail - fondement : Article L1231-1 du Code du travail
    2. Réclamation de dommages-intérêts - montant : 50 000 euros
    3. Demande de réintégration - modalités à débattre
    
    Les arguments sont sans fondement et nous proposons une réfutation complète.
    """


@pytest.fixture
def sample_arguments():
    """Arguments d'exemple pour les tests."""
    return [
        {
            "resume": "Violation du contrat",
            "risque": "Élevé",
            "fondement": "Article L1231-1",
            "justification_risque": "La jurisprudence est établie sur ce point",
            "refutations": [
                {
                    "angle": "Procédural",
                    "piste": "Demander un délai pour contre-expertise"
                }
            ]
        }
    ]


def pytest_configure(config):
    """Configuration initiale de pytest."""
    # Ajouter des marqueurs personnalisés
    config.addinivalue_line(
        "markers", "slow: marque les tests comme lents"
    )
    config.addinivalue_line(
        "markers", "integration: marque les tests d'intégration"
    )
    config.addinivalue_line(
        "markers", "unit: marque les tests unitaires"
    )
