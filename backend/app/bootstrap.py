"""
bootstrap.py — Rend importables, tels quels, les modules métier existants à
la racine du projet (analyse.py, db.py, recherche_juridique.py, judilibre.py,
extract.py, export.py, legifrance.py, paths.py) depuis le backend FastAPI,
SANS les copier ni les modifier.

Chaque fichier de app/routers/*.py et app/services/*.py qui a besoin de l'un
de ces modules doit commencer par :

    from app.bootstrap import ROOT_DIR  # noqa: F401 (garantit l'import root avant tout `import analyse` etc.)

Le garde-fou `if str(ROOT_DIR) not in sys.path` rend l'insertion idempotente :
peu importe combien de fois ce module est importé ou l'ordre d'import des
routers, la racine du projet n'est ajoutée qu'une seule fois à sys.path.
"""

import sys
from pathlib import Path

# backend/app/bootstrap.py -> parent = backend/app, parent.parent = backend,
# parent.parent.parent = racine du projet (là où vivent analyse.py, db.py...)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
