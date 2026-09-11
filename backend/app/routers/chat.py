"""
/api/chat — Chat juridique multi-tours en streaming SSE (Server-Sent Events),
avec option de recherche en direct Légifrance/Judilibre, plus la persistance
des conversations (historique, sur le modèle de Claude.ai) déjà exposée par
db.py côté tkinter.

Toute la logique métier vient telle quelle de analyse.py, recherche_juridique.py
et db.py. Les balises [ART:...]/[JURISPRUDENCE:...]/[VERIF:...] (voir
analyse.REGLE_BALISAGE_CITATIONS) ne sont jamais touchées ici : chaque
fragment brut renvoyé par analyse.repondre_conversation_stream() est
retransmis tel quel dans l'événement SSE "delta" — c'est au front de les
repérer et de les rendre visuellement, exactement comme le faisait le
tampon de gui.py pour l'ancien marqueur "À VÉRIFIER".

Important : une fois le flux SSE démarré (code HTTP 200 déjà envoyé), une
erreur ne peut plus changer le code de statut HTTP. Elle est donc transmise
comme un événement `event: error` avec un payload {"detail": "..."} — c'est
au front de l'interpréter comme une erreur, la convention JSON {detail: ...}
du reste de l'API ne s'applique qu'aux routes non-streamées.
"""

import time

from app.bootstrap import ROOT_DIR  # noqa: F401

# print() plutôt que le module logging : uvicorn ne propage pas forcément
# un logger applicatif vers la console selon sa config, alors qu'un print()
# est garanti visible dans le terminal -- l'objectif ici est un diagnostic
# immédiat pendant le débogage, pas une vraie infrastructure de logs.
def _log_chat(message: str) -> None:
    print(f"[chat] {message}", flush=True)

import analyse as legacy_analyse
import db
import recherche_juridique as legacy_rj
from app import chat_actions, demo, demo_data, quality_pipeline
from app.deps import construire_contexte_dossier, get_dossier_or_404, sse_event as _sse
from app.security_guard import executer_garde_fou
from app.schemas.chat import (
    ChatContextuelIn,
    ChatContextuelOut,
    ChatStreamIn,
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    ConversationUpdate,
)
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _construire_contexte_recherche(juridiction: str, recherche_live: bool, question: str):
    """Reproduit le contexte envoyé au modèle dans PlaidIAApp._envoyer_message_chat
    (gui.py) : le cadre juridictionnel par défaut, puis, si demandé, les
    résultats de la recherche live formatés. Retourne (contexte, n_articles, n_jurisprudence)."""
    contexte_recherche = (
        f"\n\nContexte juridictionnel par défaut réglé par l'avocat dans les paramètres : {juridiction}. "
        "Utilise ce cadre par défaut pour répondre si la question ne précise rien d'autre. "
        "Mais si la question mentionne clairement un autre pays ou système juridique, "
        "privilégie ce que la question indique explicitement plutôt que ce réglage par défaut."
    )
    n_articles = n_jurisprudence = 0
    if recherche_live:
        contexte_live = legacy_rj.rechercher_contexte_juridique(question)
        contexte_recherche += "\n\n" + legacy_rj.formater_contexte_pour_prompt(contexte_live)
        n_articles = len(contexte_live.get("articles_loi", []))
        n_jurisprudence = len(contexte_live.get("jurisprudence", []))
    return contexte_recherche, n_articles, n_jurisprudence


@router.post("/stream")
def chat_stream(payload: ChatStreamIn):
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]
    dernier_message_utilisateur = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), ""
    )

    # Résolu AVANT de démarrer le flux SSE : un dossier_id invalide doit
    # encore pouvoir renvoyer une vraie 404 JSON, ce qui n'est plus possible
    # une fois le code 200 du streaming envoyé (voir docstring du module).
    contexte_dossier = ""
    if payload.dossier_id is not None:
        dossier = get_dossier_or_404(payload.dossier_id)
        contexte_dossier = "\n\n" + construire_contexte_dossier(dossier)

    # Garde-fou d'entrée + agent de compréhension (§1-2, §10
    # ARCHITECTURE_MULTI_AGENTS.md) -- résolus ici pour la même raison que
    # dossier_id ci-dessus : security_guard.DemandeRefusee doit encore
    # pouvoir devenir une vraie réponse 422 JSON, plus possible une fois le
    # flux SSE démarré. C'est le seul endpoint où l'agent d'intention est
    # utile : contrairement à /api/analyse/conclusions ou /plan, la tâche
    # n'est pas connue à l'avance ici -- c'est l'agent d'intention qui
    # détermine dynamiquement si le trio qualité (vérificateur/critique/
    # validation finale) sera nécessaire après la génération, pour ne pas
    # l'exécuter sur une simple question conversationnelle.
    intention = None
    if not demo.mode_demo_effectif() and dernier_message_utilisateur.strip():
        historique_pour_intention = messages[:-1] if len(messages) > 1 else None
        _, intention = quality_pipeline.executer_garde_fou_et_intention(dernier_message_utilisateur, historique_pour_intention)

    def event_stream_demo():
        """Même séquence d'événements SSE que le flux réel (recherche_debut/
        recherche_resultat simulés si demandé, puis delta mot à mot, puis
        done) mais avec une réponse préenregistrée -- indiscernable côté
        front, voir demo_data.py::reponse_demo_pour_question."""
        nb_fragments = 0
        _log_chat(f"debut du flux (mode demo, dossier_id={payload.dossier_id}, recherche_live={payload.recherche_live})")
        try:
            if payload.recherche_live:
                yield _sse("recherche_debut", {})
                time.sleep(0.3)
                yield _sse("recherche_resultat", {"n_articles": 0, "n_jurisprudence": 0})

            reponse = demo_data.reponse_demo_pour_question(dernier_message_utilisateur)
            mots = reponse.split(" ")
            for i, mot in enumerate(mots):
                fragment = mot if i == len(mots) - 1 else mot + " "
                yield _sse("delta", {"text": fragment})
                nb_fragments += 1
                time.sleep(0.02)

            yield _sse("done", {})
        except Exception as e:
            _log_chat(f"erreur en cours de flux (mode demo) : {e}")
            yield _sse("error", {"detail": str(e)})
        finally:
            _log_chat(f"fin du flux (mode demo) -- {nb_fragments} fragment(s) envoyé(s)")

    def event_stream():
        nb_fragments = 0
        _log_chat(f"debut du flux (mode reel, dossier_id={payload.dossier_id}, recherche_live={payload.recherche_live})")
        try:
            if payload.recherche_live:
                yield _sse("recherche_debut", {})
                contexte_recherche, n_articles, n_jurisprudence = _construire_contexte_recherche(
                    payload.juridiction, True, dernier_message_utilisateur
                )
                yield _sse("recherche_resultat", {"n_articles": n_articles, "n_jurisprudence": n_jurisprudence})
            else:
                contexte_recherche, _, _ = _construire_contexte_recherche(payload.juridiction, False, "")
            contexte_recherche += contexte_dossier

            fragments_accumules = []
            for fragment in legacy_analyse.repondre_conversation_stream(messages, contexte_recherche=contexte_recherche):
                fragments_accumules.append(fragment)
                yield _sse("delta", {"text": fragment})
                nb_fragments += 1

            # Trio qualité (§10), seulement si l'agent d'intention l'a jugé
            # nécessaire -- événement SSE additif "verification", envoyé
            # AVANT "done" pour que le front puisse l'associer au message en
            # cours de finalisation plutôt qu'à un message déjà sauvegardé.
            # Un front qui ignore cet événement n'est pas affecté.
            if intention is not None:
                texte_reponse = "".join(fragments_accumules)
                verification = quality_pipeline.executer_trio_qualite_si_necessaire(
                    texte_reponse,
                    intention,
                    sources_textes=[contexte_recherche] if payload.recherche_live else None,
                    contexte_dossier=contexte_dossier,
                )
                if verification is not None:
                    yield _sse("verification", verification)

            yield _sse("done", {})
        except Exception as e:
            _log_chat(f"erreur en cours de flux (mode reel) : {e}")
            yield _sse("error", {"detail": str(e)})
        finally:
            _log_chat(f"fin du flux (mode reel) -- {nb_fragments} fragment(s) envoyé(s)")

    generateur = event_stream_demo() if demo.mode_demo_effectif() else event_stream()
    return StreamingResponse(
        generateur,
        media_type="text/event-stream",
        headers={
            # Empêche tout proxy/serveur intermédiaire (Render, Nginx...) de
            # mettre le flux en tampon avant de le relâcher d'un coup --
            # sans ça, le navigateur peut sembler "bloqué" jusqu'à ce que le
            # tampon se vide, même si le backend envoie bien ses trames au
            # fil de l'eau. Sans effet en dev local direct (pas de proxy
            # entre uvicorn et le navigateur), mais nécessaire derrière tout
            # reverse proxy -- voir DEPLOIEMENT.md.
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# --- Chat contextuel (édition d'un résultat déjà affiché) -----------------
# Voir ARCHITECTURE_CHAT_CONTEXTUEL.md. Contrairement à /stream ci-dessus,
# pas de SSE ici : la réponse doit être validée en entier (app.chat_actions)
# avant de pouvoir en renvoyer quoi que ce soit d'exploitable -- un flux
# caractère par caractère n'apporterait rien pour un JSON qui doit rester
# valide, et complique la validation côté serveur pour rien.

@router.post("/contextuel", response_model=ChatContextuelOut)
def chat_contextuel(payload: ChatContextuelIn):
    demo.exiger_cle_api()

    # Garde-fou d'entrée seulement (§1, §9) -- pas le trio qualité complet
    # ici : une édition locale est déjà protégée par la validation de
    # app.chat_actions (le modèle propose un scope/une opération, le code
    # vérifie qu'ils correspondent réellement au résultat affiché avant de
    # rien appliquer), donc ajouter vérificateur/critique/validation finale
    # sur chaque petite modification serait disproportionné.
    executer_garde_fou(payload.message)

    contexte_dossier = ""
    if payload.dossier_id is not None:
        dossier = get_dossier_or_404(payload.dossier_id)
        contexte_dossier = construire_contexte_dossier(dossier)
    if payload.document_id is not None:
        document = db.get_document_genere(payload.document_id)
        if not document or document["dossier_id"] != payload.dossier_id:
            raise HTTPException(status_code=404, detail=f"Document {payload.document_id} introuvable dans ce dossier.")
        try:
            db.verifier_document_modifiable(payload.document_id)
        except db.DocumentFinalError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    historique = [{"role": m.role, "content": m.content} for m in payload.historique]

    action = legacy_analyse.traiter_message_edition(
        feature=payload.feature,
        message=payload.message,
        resultat_actuel=payload.resultat_actuel,
        contexte_dossier=contexte_dossier,
        historique=historique,
    )

    resultat_modifie = None
    if action["intent"] in ("modify", "add", "delete"):
        try:
            chat_actions.valider_action(payload.feature, action["scope"], action["operation"], payload.resultat_actuel)
            if payload.feature == "conclusions" and payload.resultat_actuel.get("analyse_id") is not None:
                try:
                    db.verifier_analyse_modifiable(payload.resultat_actuel["analyse_id"])
                except db.DocumentFinalError as e:
                    raise HTTPException(status_code=409, detail=str(e)) from e
            resultat_modifie = chat_actions.appliquer_patch(
                payload.resultat_actuel, action["scope"], action["operation"], action["contenu_modifie"]
            )
            if payload.document_id is not None:
                db.mettre_a_jour_document_genere(payload.document_id, resultat_modifie)
            # Versioning (§8 de la demande, AUDIT_TASKBAR.md étape 4) : le
            # patch vient d'être validé ET appliqué -- c'est précisément le
            # moment où une nouvelle version du résultat naît. Jamais
            # bloquant : un échec d'écriture ici ne doit jamais faire
            # échouer une édition qui a par ailleurs réussi.
            try:
                db.enregistrer_version(
                    payload.dossier_id, payload.feature, resultat_modifie, resume_modification=action["reponse_agent"], auteur="ia", document_id=payload.document_id
                )
            except Exception as e:
                _log_chat(f"échec de l'enregistrement de la version (non bloquant) : {e}")
        except chat_actions.ActionInvalide as e:
            # Le modèle a proposé une action qui ne correspond pas au
            # résultat réel -- jamais appliquée, jamais renvoyée comme si
            # elle l'avait été. On informe l'utilisateur au lieu de planter.
            _log_chat(f"action refusée par chat_actions : {e}")
            return ChatContextuelOut(
                intent="clarification",
                scope="global",
                operation="none",
                parameters={},
                resultat_modifie=None,
                reponse_agent=f"Je n'ai pas pu appliquer cette modification ({e}). Pouvez-vous préciser votre demande ?",
            )

    return ChatContextuelOut(
        intent=action["intent"],
        scope=action["scope"],
        operation=action["operation"],
        parameters=action.get("parameters") or {},
        resultat_modifie=resultat_modifie,
        reponse_agent=action["reponse_agent"],
    )


# --- Historique des conversations (persistance, sauvegarde côté front) ----

@router.get("/conversations", response_model=list[ConversationOut])
def lister_conversations():
    return db.lister_conversations_chat()


@router.get("/conversations/dossier/{dossier_id}", response_model=list[ConversationOut])
def lister_conversations_dossier(dossier_id: int):
    get_dossier_or_404(dossier_id)
    return db.lister_conversations_chat_par_dossier(dossier_id)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def obtenir_conversation(conversation_id: int):
    conversation = db.get_conversation_chat(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} introuvable.")
    return conversation


@router.post("/conversations", response_model=ConversationOut, status_code=201)
def creer_conversation(payload: ConversationCreate):
    if payload.dossier_id is not None:
        get_dossier_or_404(payload.dossier_id)
    historique = [m.model_dump() for m in payload.historique]
    conversation_id = db.creer_conversation_chat(payload.titre, historique, payload.dossier_id)
    return next(c for c in db.lister_conversations_chat() if c["id"] == conversation_id)


@router.put("/conversations/{conversation_id}", response_model=ConversationOut)
def mettre_a_jour_conversation(conversation_id: int, payload: ConversationUpdate):
    if not db.get_conversation_chat(conversation_id):
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} introuvable.")
    historique = [m.model_dump() for m in payload.historique]
    db.mettre_a_jour_conversation_chat(conversation_id, historique)
    return next(c for c in db.lister_conversations_chat() if c["id"] == conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
def supprimer_conversation(conversation_id: int):
    db.supprimer_conversation_chat(conversation_id)
