/**
 * useChatContextuel — logique du chat contextuel (voir
 * ARCHITECTURE_CHAT_CONTEXTUEL.md §2.5). Générique : ne connaît rien du
 * contenu de `resultatActuel`, seulement son `feature` (identifiant pour
 * le backend) — c'est POST /api/chat/contextuel + app/chat_actions.py
 * côté serveur qui savent lire/écrire la forme réelle du résultat.
 *
 * Historique tenu ici, local à ce panneau (pas le store global du Chat
 * juridique) : chaque page de génération a son propre fil de discussion
 * sur SON résultat, remis à zéro si la page régénère un nouveau résultat
 * (voir ChatContextuelPanel::useEffect sur resultatActuel).
 */

import { useState } from "react";
import { chat as chatApi } from "@/api";
import type { FeatureChatContextuel, MessageChat } from "@/api";
import { useAppStore } from "@/store/useAppStore";

export function useChatContextuel<T>(
  feature: FeatureChatContextuel,
  resultatActuel: T,
  onMiseAJour: (nouveauResultat: T) => void,
  dossierId?: number | null,
  documentId?: number | null
) {
  const [messages, setMessages] = useState<MessageChat[]>([]);
  const [loading, setLoading] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const envoyer = async (texte: string) => {
    const contenu = texte.trim();
    if (!contenu || loading) return;

    const historiquePrecedent = messages;
    setMessages((m) => [...m, { role: "user", content: contenu }]);
    setLoading(true);
    setErreur(null);

    try {
      const resultat = await chatApi.envoyerMessageContextuel(feature, contenu, resultatActuel, historiquePrecedent, dossierId, documentId);
      setMessages((m) => [...m, { role: "assistant", content: resultat.reponse_agent }]);
      if (resultat.resultat_modifie !== null && resultat.resultat_modifie !== undefined) {
        onMiseAJour(resultat.resultat_modifie as T);
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Une erreur est survenue.";
      setErreur(message);
      pousserToast("error", message);
      // Le message utilisateur reste affiché (comme ChatPage) -- seule la
      // réponse manque, pas de retour arrière silencieux sur ce qui a été dit.
    } finally {
      setLoading(false);
    }
  };

  const reinitialiser = () => {
    setMessages([]);
    setErreur(null);
  };

  return { messages, loading, erreur, envoyer, reinitialiser };
}
