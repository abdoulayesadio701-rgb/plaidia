"""
paths.py — Détermine le dossier de référence pour les fichiers de config
(apikey.txt, judilibre_key.txt...) et la base de données, que le programme
soit lancé comme script Python normal OU comme .exe empaqueté (PyInstaller).
"""

import sys
from pathlib import Path


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        # Lancé comme .exe empaqueté : utiliser le dossier de l'exécutable
        return Path(sys.executable).parent
    # Lancé comme script Python normal
    return Path(__file__).parent
