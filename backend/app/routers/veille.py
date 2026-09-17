"""
/api/veille — Notifications de veille (jurisprudence + lois) pour le
backend web. Voir backend/app/veille.py pour la boucle périodique, et
db.py (tables alertes_jurisprudence_dossier, alertes_articles_dossier)
pour la persistance -- portage de gui.py::DialogueNotificationsVeille /
DialogueAlertesArticles, mêmes principes : jamais de suppression
automatique, acquittement uniquement sur action explicite.
"""

from app.bootstrap import ROOT_DIR  # noqa: F401

import db
import veille_lois
from app import veille as veille_serveur
from app.schemas.veille import NotificationsVeilleOut
from fastapi import APIRouter

router = APIRouter(prefix="/api/veille", tags=["veille"])


@router.get("/notifications", response_model=NotificationsVeilleOut)
def notifications(dossier_id: int | None = None):
    """Alertes actives (non acquittées), globalement ou pour un dossier
    précis. Alimente le badge 🔔 du bandeau (global, sans dossier_id) et
    le signal de la fiche dossier (avec dossier_id) -- même distinction
    que côté gui.py entre bouton_veille et bouton_alerte_dossier."""
    return NotificationsVeilleOut(
        jurisprudence=db.get_alertes_jurisprudence_actives(dossier_id),
        lois=db.get_alertes_actives_dossier(dossier_id),
        rappel_ohada=veille_lois.rappel_veille_ohada(),
    )


@router.post("/verifier", status_code=202)
def declencher_verification():
    """Déclenche un passage de veille immédiat plutôt que d'attendre la
    prochaine itération de la boucle horaire (voir backend/app/veille.py).
    Ignoré silencieusement (renvoie quand même 202) si un passage tourne
    déjà, ou en mode démo serveur -- jamais d'erreur pour ça, ce n'est
    qu'un raccourci."""
    veille_serveur.executer_un_passage()
    return {"detail": "Vérification lancée (ou déjà en cours)."}


@router.post("/jurisprudence/{alerte_id}/acquitter", status_code=204)
def acquitter_jurisprudence(alerte_id: int):
    db.acquitter_alerte_jurisprudence(alerte_id)


@router.post("/lois/{alerte_id}/acquitter", status_code=204)
def acquitter_loi(alerte_id: int):
    db.acquitter_alerte_article(alerte_id)


@router.post("/ohada/marquer-verifie", status_code=204)
def marquer_ohada_verifie():
    """Confirmation manuelle explicite que le corpus OHADA a été revérifié
    contre la source officielle -- jamais automatique (voir
    veille_lois.marquer_veille_ohada_verifiee)."""
    veille_lois.marquer_veille_ohada_verifiee()
