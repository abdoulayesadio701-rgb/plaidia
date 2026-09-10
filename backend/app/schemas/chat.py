"""Schémas Pydantic pour le router /api/chat (streaming SSE)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.demo import MAX_TEXTE_CARACTERES

# Pas de max_length ici : MessageChat sert aussi bien à valider un nouveau
# message entrant qu'à sérialiser une conversation déjà enregistrée en
# sortie (GET /conversations/{id}) -- un plafond y casserait la lecture de
# conversations plus anciennes et plus longues que la limite. La protection
# anti-abus porte sur le dernier message envoyé, via ChatStreamIn ci-dessous.


class MessageChat(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatStreamIn(BaseModel):
    messages: list[MessageChat] = Field(..., min_length=1, description="Historique complet, le dernier message étant la question courante")
    recherche_live: bool = Field(False, description="Active la recherche en direct Légifrance/Judilibre avant de répondre")
    juridiction: str = Field("Légifrance (France)", description="Juridiction par défaut à utiliser si la question ne précise rien")
    dossier_id: Optional[int] = Field(
        None, description="Si fourni, le contexte du dossier (faits, parties, dernière analyse) est ajouté au contexte envoyé au modèle"
    )

    @field_validator("messages")
    @classmethod
    def limiter_taille_dernier_message(cls, messages: list[MessageChat]) -> list[MessageChat]:
        # Seul le dernier message (celui que l'utilisateur vient de saisir)
        # est plafonné -- l'historique déjà échangé n'est pas de son fait.
        if messages and len(messages[-1].content) > MAX_TEXTE_CARACTERES:
            raise ValueError(f"Le message est trop long ({len(messages[-1].content)} caractères, {MAX_TEXTE_CARACTERES} maximum).")
        return messages


class ConversationCreate(BaseModel):
    titre: str = Field(..., min_length=1)
    historique: list[MessageChat]
    dossier_id: Optional[int] = None


class ConversationUpdate(BaseModel):
    historique: list[MessageChat]


class ConversationOut(BaseModel):
    id: int
    titre: str
    date_creation: str
    date_modification: str
    dossier_id: Optional[int] = None


class ConversationDetailOut(BaseModel):
    id: int
    titre: str
    date_creation: str
    date_modification: str
    dossier_id: Optional[int] = None
    historique: list[MessageChat]


# --- Chat contextuel (édition d'un résultat déjà affiché) ------------------
# Voir ARCHITECTURE_CHAT_CONTEXTUEL.md — un seul mécanisme réutilisé par
# toutes les pages de génération (Arsenal/Greffier/Carnet), pas un chat par
# fonctionnalité.

class ChatContextuelIn(BaseModel):
    feature: str = Field(
        ..., description="Identifiant de la fonctionnalité en cours : conclusions, plan, simulateur, note_client, chronologie, coherence, pv_audience, rapport_complet..."
    )
    dossier_id: Optional[int] = Field(None, description="Si fourni, le contexte du dossier est ajouté (mêmes règles que /api/chat/stream)")
    resultat_actuel: dict = Field(..., description="Le résultat actuellement affiché à l'écran, tel quel")
    message: str = Field(..., min_length=1, max_length=MAX_TEXTE_CARACTERES)
    historique: list[MessageChat] = Field([], description="Échanges précédents de CE fil contextuel (pas celui du Chat juridique général)")


class ChatContextuelOut(BaseModel):
    intent: str
    scope: str
    operation: str
    parameters: dict = {}
    resultat_modifie: Optional[dict] = Field(None, description="Le résultat complet, déjà patché — à substituer tel quel à l'ancien côté front")
    reponse_agent: str
