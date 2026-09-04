"""
/api/intention — Interprétation d'une commande en langage naturel (barre de
commande de gui.py), pour router côté front vers la bonne action.

Toute la logique métier vient telle quelle de analyse.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import analyse as legacy_analyse
from app import demo
from app.schemas.intention import IntentionIn, IntentionOut
from fastapi import APIRouter

router = APIRouter(prefix="/api/intention", tags=["intention"])


@router.post("/interpreter", response_model=IntentionOut)
def interpreter(payload: IntentionIn):
    if demo.mode_demo_effectif():
        # Pas d'appel bloquant en 503 ici : la CommandBar sait déjà gérer
        # une confiance basse avec un message d'orientation vers la
        # sidebar -- une bien meilleure expérience de démo qu'une erreur.
        return IntentionOut(action="menu", confiance="basse", reformulation="", duree_minutes=None)
    return legacy_analyse.interpreter_intention(payload.texte)
