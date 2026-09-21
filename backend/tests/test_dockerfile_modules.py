"""
test_dockerfile_modules.py — Garde-fou contre un déploiement qui plante au
démarrage : le Dockerfile copie les modules métier de la racine UN PAR UN
(jamais `COPY . .`, voir backend/Dockerfile). Un module racine importé par
le backend (ou par un autre module copié) mais absent de cette liste passe
tous les tests en local et fait échouer le démarrage sur Render avec un
`ModuleNotFoundError` -- c'est arrivé avec usage_log.py et veille_lois.py.
"""

import ast
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
DOCKERFILE = RACINE / "backend" / "Dockerfile"


def _modules_copies() -> set[str]:
    # Ligne "COPY a.py b.py ... ./" (modules racine), pas les COPY de dossiers.
    for ligne in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("COPY ") and ligne.rstrip().endswith("./") and ".py" in ligne:
            return {Path(p).stem for p in ligne.split()[1:-1] if p.endswith(".py")}
    raise AssertionError("Aucune ligne COPY de modules .py trouvée dans le Dockerfile")


def _imports_racine(fichier: Path, modules_racine: set[str]) -> set[str]:
    arbre = ast.parse(fichier.read_text(encoding="utf-8"))
    trouves = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            trouves |= {a.name.split(".")[0] for a in noeud.names}
        elif isinstance(noeud, ast.ImportFrom) and noeud.level == 0 and noeud.module:
            trouves.add(noeud.module.split(".")[0])
    return trouves & modules_racine


def test_tous_les_modules_racine_utilises_sont_copies_dans_l_image_docker():
    modules_racine = {p.stem for p in RACINE.glob("*.py")}
    copies = _modules_copies()

    # Code de l'API (hors scripts/, outils d'import ponctuels non lancés par
    # le serveur) + modules racine déjà copiés (ex. analyse.py -> usage_log.py).
    a_analyser = [p for p in (RACINE / "backend" / "app").rglob("*.py") if "scripts" not in p.parts]
    a_analyser += [RACINE / f"{m}.py" for m in copies if (RACINE / f"{m}.py").exists()]

    requis: set[str] = set()
    for fichier in a_analyser:
        requis |= _imports_racine(fichier, modules_racine)

    manquants = sorted(requis - copies)
    assert not manquants, (
        f"Modules racine importés mais absents du COPY de backend/Dockerfile : {manquants}. "
        "Ajoutez-les à la ligne `COPY analyse.py db.py ... ./`."
    )
