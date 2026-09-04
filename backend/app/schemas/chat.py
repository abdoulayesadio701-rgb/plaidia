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


class ConversationUpdate(BaseModel):
    historique: list[MessageChat]


class ConversationOut(BaseModel):
    id: int
    titre: str
    date_creation: str
    date_modification: str


class ConversationDetailOut(BaseModel):
    id: int
    titre: str
    date_creation: str
    date_modification: str
    historique: list[MessageChat]
