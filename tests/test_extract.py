#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_extract.py — Tests unitaires pour le module extract.py
"""

import pytest
import tempfile
from pathlib import Path


class TestExtractText:
    """Tests pour l'extraction de texte."""
    
    def test_extract_txt(self):
        """Test l'extraction de texte depuis un fichier TXT."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from extract import extract_text
        
        # Créer un fichier TXT temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Ceci est un texte de test.\nAvec plusieurs lignes.\n")
            temp_path = f.name
        
        try:
            text = extract_text(temp_path)
            assert "texte de test" in text
            assert "plusieurs lignes" in text
        finally:
            Path(temp_path).unlink()
    
    def test_extract_txt_unicode(self):
        """Test l'extraction de texte avec caractères spéciaux."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from extract import extract_text
        
        # Créer un fichier TXT avec caractères français
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Analyse juridique : prud'hommes, contrat, rémunération.\n")
            temp_path = f.name
        
        try:
            text = extract_text(temp_path)
            assert "prud'hommes" in text
            assert "rémunération" in text
        finally:
            Path(temp_path).unlink()


class TestCleanText:
    """Tests pour le nettoyage de texte."""
    
    def test_clean_text_removes_blank_lines(self):
        """Vérifie que _clean_text supprime les lignes vides."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from extract import _clean_text
        
        text = "Ligne 1\n\n\nLigne 2\n\n\nLigne 3"
        cleaned = _clean_text(text)
        
        # Pas plus de 1 ligne vide consécutive
        assert "\n\n\n" not in cleaned
    
    def test_clean_text_preserves_content(self):
        """Vérifie que _clean_text préserve le contenu."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from extract import _clean_text
        
        text = "Contenu important à préserver"
        cleaned = _clean_text(text)
        
        assert "Contenu important" in cleaned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
