#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_db.py — Tests unitaires pour le module db.py
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
import json

# Pour les tests, on va tester en isolation avec une DB temporaire


@pytest.fixture
def temp_db():
    """Crée une base de données temporaire pour les tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        # Importer après la fixture pour éviter les problèmes
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        import db
        # Modifier temporairement le chemin de la DB
        original_db_path = db.DB_PATH
        db.DB_PATH = db_path
        
        # Initialiser
        db.init_db()
        
        yield db, db_path
        
        # Restaurer
        db.DB_PATH = original_db_path


class TestDatabase:
    """Tests pour les opérations de base de données."""
    
    def test_init_db_creates_file(self, temp_db):
        """Vérifie que init_db crée la base de données."""
        db, db_path = temp_db
        assert db_path.exists()
    
    def test_init_db_creates_tables(self, temp_db):
        """Vérifie que toutes les tables sont créées."""
        db, db_path = temp_db
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier les tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['dossiers', 'analyses', 'jurisprudence', 'trames']
        for table in expected_tables:
            assert table in tables, f"Table {table} manquante"
        
        conn.close()
    
    def test_create_dossier(self, temp_db):
        """Teste la création d'un dossier."""
        db, _ = temp_db
        
        dossier_id = db.create_dossier(
            nom="Test dossier",
            domaine="prud'hommes",
            parties="A vs B",
            faits="Test faits"
        )
        
        assert dossier_id > 0
    
    def test_get_dossier(self, temp_db):
        """Teste la récupération d'un dossier."""
        db, _ = temp_db
        
        created_id = db.create_dossier(
            nom="Test dossier",
            domaine="prud'hommes",
            parties="A vs B",
            faits="Test faits"
        )
        
        dossier = db.get_dossier(created_id)
        assert dossier is not None
        assert dossier["nom"] == "Test dossier"
        assert dossier["domaine"] == "prud'hommes"
    
    def test_list_dossiers(self, temp_db):
        """Teste la liste des dossiers."""
        db, _ = temp_db
        
        # Créer plusieurs dossiers
        db.create_dossier("Dossier 1", "prud'hommes", "A", "Test")
        db.create_dossier("Dossier 2", "penal", "B", "Test")
        
        dossiers = db.list_dossiers()
        assert len(dossiers) >= 2


class TestAnalysis:
    """Tests pour les analyses."""
    
    def test_save_analyse(self, temp_db):
        """Teste la sauvegarde d'une analyse."""
        db, _ = temp_db
        
        # Créer un dossier
        dossier_id = db.create_dossier(
            "Test dossier", "prud'hommes", "A vs B", "Test"
        )
        
        # Créer une analyse
        arguments = [
            {
                "resume": "Argument 1",
                "risque": "Élevé",
                "fondement": "Code du travail",
                "refutations": []
            }
        ]
        points_attention = ["Point 1", "Point 2"]
        
        analyse_id = db.save_analyse(
            dossier_id,
            arguments,
            points_attention
        )
        
        assert analyse_id > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
