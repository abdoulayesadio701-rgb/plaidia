"""
backend/app/veille.py — Veille jurisprudence + lois pour le backend web.

Porte gui.py::PlaidIAApp._lancer_verification_veille /
_lancer_verification_veille_lois côté serveur : un thread démarré une
seule fois au lancement du serveur (voir main.py, lifespan), qui boucle
toutes les INTERVALLE_VEILLE_SECONDES tant que le processus vit.

Différence assumée avec gui.py : une seule instance de serveur sert
potentiellement plusieurs rechargements de page/onglets, donc les
notifications détectées sont PERSISTÉES (db.alertes_jurisprudence_dossier,
db.alertes_articles_dossier) plutôt que gardées dans une liste en mémoire
propre à une session Tkinter unique -- voir le commentaire sur
CREATE TABLE alertes_jurisprudence_dossier dans db.py.

Ne modifie jamais gui.py::_lancer_verification_veille ni son
fonctionnement -- ce module est un portage parallèle, pas un partage de
code avec l'implémentation Tkinter (même mécanique, même tables
db.elements_veille_vus/db.alertes_articles_dossier, code séparé)."""

import threading
import time

import db
import judilibre
import veille_lois
from app import demo

INTERVALLE_VEILLE_SECONDES = 60 * 60  # 1 heure -- même fréquence que gui.py::PlaidIAApp.INTERVALLE_VEILLE_MS

_verification_en_cours = threading.Lock()  # évite deux passages superposés (déclenchement manuel + boucle)


def verifier_jurisprudence() -> None:
    """Équivalent serveur de gui.py::_lancer_verification_veille -- mêmes
    fonctions de dédup (db.get_references_vues/marquer_references_vues),
    mais persiste une alerte (db.creer_alerte_jurisprudence) plutôt qu'un
    badge éphémère en mémoire."""
    try:
        dossiers_actifs = [dict(d) for d in db.list_dossiers() if d["statut"] == "en cours" and d["domaine"]][:5]
    except Exception:
        return
    for d in dossiers_actifs:
        try:
            resultats = judilibre.collecter_jurisprudence(query=d["domaine"], max_results=5)
        except Exception:
            continue
        deja_vues = db.get_references_vues(d["id"])
        references_ce_dossier = []
        for r in resultats:
            references_ce_dossier.append(r["reference"])
            if r["reference"] not in deja_vues:
                db.creer_alerte_jurisprudence(d["id"], r["reference"], r["resume"], r["source"])
        db.marquer_references_vues(d["id"], references_ce_dossier)


def verifier_lois() -> None:
    """Équivalent serveur de gui.py::_lancer_verification_veille_lois."""
    try:
        dossiers_actifs = [dict(d) for d in db.list_dossiers() if d["statut"] == "en cours"]
    except Exception:
        return

    # 1) Réextrait les articles [ART:...] cités par chaque dossier actif.
    for d in dossiers_actifs:
        try:
            textes = [d.get("faits") or ""]
            for a in db.get_analyses_for_dossier(d["id"]):
                textes.append(str(a.get("arguments") or ""))
                textes.append(str(a.get("points_attention") or ""))
            for g in db.list_generations(dossier_id=d["id"]):
                textes.append(str(g.get("contenu") or ""))
            for n in db.get_notes_dossier(d["id"]):
                textes.append(n.get("note_structuree") or "")
            db.remplacer_articles_cites_dossier(d["id"], veille_lois.extraire_articles_cites(*textes))
        except Exception:
            continue

    # 2) Une seule vérification Légifrance par article distinct.
    try:
        articles = db.tous_articles_cites()
    except Exception:
        articles = []
    for code, numero in articles:
        try:
            changement = veille_lois.verifier_et_detecter_changement(code, numero)
        except Exception:
            continue
        if not changement:
            continue
        for dc in db.lister_dossiers_citant_article(code, numero):
            db.creer_alerte_article(
                dc["id"], code, numero,
                changement["ancien_etat"], changement["nouvel_etat"],
                changement["date_modification"], changement["lien"],
            )


def executer_un_passage() -> bool:
    """Un passage complet des deux veilles -- appelé par la boucle
    périodique ci-dessous, ou directement depuis POST /api/veille/verifier
    (déclenchement manuel). Jamais en mode démo serveur (voir
    demo.mode_demo_serveur) : un déploiement de démonstration public n'a
    pas à consommer le quota Judilibre/Légifrance pour un dossier fictif.
    Renvoie False si un passage était déjà en cours (ignoré plutôt que
    superposé) ou si le mode démo l'a court-circuité."""
    if demo.mode_demo_serveur():
        return False
    if not _verification_en_cours.acquire(blocking=False):
        return False
    try:
        verifier_jurisprudence()
        verifier_lois()
        return True
    finally:
        _verification_en_cours.release()


def demarrer_boucle_veille() -> None:
    """Démarre le thread de veille périodique -- appelé une seule fois, au
    démarrage du serveur (voir main.py, lifespan). daemon=True : ne
    retient jamais l'arrêt du processus."""
    def boucle():
        while True:
            executer_un_passage()
            time.sleep(INTERVALLE_VEILLE_SECONDES)

    threading.Thread(target=boucle, daemon=True).start()
