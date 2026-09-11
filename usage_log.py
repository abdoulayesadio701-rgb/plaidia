"""
usage_log.py — Journalisation légère de l'usage des modèles (chantier
"optimisation des coûts API", tâche 5) : un fichier JSON-lines,
un enregistrement par appel, pour pouvoir reconstituer après coup la
répartition des coûts par fournisseur/tâche sans toucher au reste du
code (aucune base de données, aucune dépendance nouvelle).

Ne lève jamais : une panne d'écriture de log ne doit jamais faire
échouer l'appel API réel qu'elle décrit -- même idiome de tolérance que
`_appel_protege` dans backend/app/quality_pipeline.py.
"""

import json
import time

import paths

LOG_FILE = paths.base_dir() / "logs" / "usage_api.jsonl"


def journaliser_usage(fournisseur: str, tache: str, modele: str, tokens_entree: int, tokens_sortie: int) -> None:
    """Ajoute une ligne JSON au journal d'usage. `fournisseur` : "claude" ou
    "deepseek" (label produit -- même si le transport réel d'un fournisseur
    peut être un hébergeur tiers, voir analyse.py::_client_deepseek).
    `tache` : la valeur de analyse.TypeTache (ex. "extraction", "resume")."""
    enregistrement = {
        "horodatage": time.time(),
        "fournisseur": fournisseur,
        "tache": tache,
        "modele": modele,
        "tokens_entree": tokens_entree,
        "tokens_sortie": tokens_sortie,
    }
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(enregistrement, ensure_ascii=False) + "\n")
    except OSError:
        pass
