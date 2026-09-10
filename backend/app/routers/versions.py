"""
/api/versions — Historique des versions d'un résultat édité via le chat
contextuel (voir AUDIT_TASKBAR.md, étape 4 ; ARCHITECTURE_CHAT_CONTEXTUEL.md).
Une version est créée automatiquement à chaque patch appliqué avec succès
par chat_actions (voir routers/chat.py::chat_contextuel) -- ce router ne
fait que lire cet historique et permettre une restauration, qui elle-même
ne fait qu'ajouter une nouvelle version (jamais de suppression).
"""

import json

from app.bootstrap import ROOT_DIR  # noqa: F401

import db
from app.schemas.versions import VersionOut
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/versions", tags=["versions"])


def _vers_sortie(row) -> dict:
    d = dict(row)
    d["contenu"] = json.loads(d.pop("contenu_json"))
    return d


@router.get("/", response_model=list[VersionOut])
def lister(feature: str, dossier_id: int | None = None, document_id: int | None = None):
    return [_vers_sortie(v) for v in db.lister_versions(feature, dossier_id, document_id)]


@router.post("/{version_id}/restaurer", response_model=VersionOut)
def restaurer(version_id: int):
    nouvelle_version = db.restaurer_version(version_id)
    if not nouvelle_version:
        raise HTTPException(status_code=404, detail=f"Version {version_id} introuvable.")
    return _vers_sortie(nouvelle_version)
