"""
/api/intention — Interprétation d'une commande en langage naturel (barre de
commande de gui.py), pour router côté front vers la bonne action.

Toute la logique métier vient telle quelle de analyse.py.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import analyse as legacy_analyse
from app import demo, demo_data_outils
from app.schemas.intention import IntentionIn, IntentionOut
from fastapi import APIRouter

router = APIRouter(prefix="/api/intention", tags=["intention"])


@router.post("/interpreter", response_model=IntentionOut)
def interpreter(payload: IntentionIn):
    if demo.mode_demo_effectif():
        # Interprétation par mots-clés, sans modèle (voir demo_data_outils) :
        # l'exemple affiché dans la barre (« établir un plan de 10 minutes »)
        # doit fonctionner. Sans correspondance : confiance basse, que la
        # CommandBar traduit par une orientation vers la sidebar.
        return IntentionOut(**demo_data_outils.intention_demo(payload.texte))
    return legacy_analyse.interpreter_intention(payload.texte)
