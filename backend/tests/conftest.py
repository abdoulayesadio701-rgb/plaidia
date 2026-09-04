"""
conftest.py — Configuration des tests backend.

⚠️ CRITIQUE — lire avant de modifier ce fichier :

Les variables d'environnement ci-dessous DOIVENT être positionnées avant
tout import de `db`, `app.demo` ou `app.main` : leurs constantes de module
(`db.DB_PATH`, `app.demo.DEMO_MODE_FORCE`...) sont calculées UNE SEULE FOIS
à l'import, pas relues à chaque requête. C'est pour ça que ce bloc est
placé tout en haut du fichier, avant même les imports pytest -- conftest.py
est chargé par pytest avant les modules de test du même dossier, donc ce
code s'exécute avant qu'aucun test n'importe quoi que ce soit de `app`.

Sans cette protection, les tests utiliseraient la vraie base de données du
poste (`plaidoirie.db`, ou celle du serveur en CI) au lieu d'un fichier
jetable -- exactement l'incident qui a effacé des dossiers de test réels
lors d'une session de développement précédente de ce projet. Ne retirez
JAMAIS ce bloc, et ne réordonnez jamais les imports en dessous.
"""

import os
import sys
import tempfile
from pathlib import Path

_TMP_DB_DIR = tempfile.mkdtemp(prefix="plaidia_test_")
os.environ["PLAIDIA_DB_PATH"] = str(Path(_TMP_DB_DIR) / "test_plaidoirie.db")
os.environ["DEMO_MODE"] = "true"
os.environ["DEMO_RESET_DB"] = "true"
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
# Évite que le volume de requêtes du test suite lui-même ne déclenche le
# limiteur de débit (voir main.py, slowapi) -- le comportement du limiteur
# n'est pas ce que cette suite minimale cherche à couvrir.
os.environ["RATE_LIMIT_DEFAUT"] = "100000/minute"
# Neutralise toute vraie clé API qui traînerait dans l'environnement de la
# personne qui lance les tests -- le mode démo doit s'appliquer quoi qu'il
# arrive pendant les tests (voir DEMO_MODE=true ci-dessus, qui suffit déjà
# en théorie, mais on ne veut prendre aucun risque d'appel réel à Claude).
os.environ.pop("ANTHROPIC_API_KEY", None)

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    """Un TestClient par test : le lifespan (voir main.py) réinitialise la
    base jetable à chaque entrée dans le `with`, donc chaque test démarre
    sur un état propre (le seul dossier fictif de démo, rien d'autre)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def dossier_demo_id(client: TestClient) -> int:
    """Id du dossier fictif de démonstration, réensemencé à chaque test."""
    dossiers = client.get("/api/dossiers/").json()
    assert len(dossiers) == 1, "Le mode démo ne devrait ensemencer qu'un seul dossier fictif."
    return dossiers[0]["id"]
