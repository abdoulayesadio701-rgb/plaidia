/**
 * ChatContextuelPanel — panneau générique "Demander à l'agent", à poser
 * sous n'importe quel résultat déjà affiché (voir
 * ARCHITECTURE_CHAT_CONTEXTUEL.md §2.5 et §1.1-1.2 pour la liste des pages
 * concernées). Un seul composant, réutilisé tel quel par chaque page --
 * ce qui change d'une page à l'autre, c'est seulement `feature` et
 * `resultatActuel`.
 *
 * Fermé par défaut, discret : un simple bouton texte sous le résultat.
 * Ne s'affiche jamais sur une page qui n'a pas encore de résultat --
 * c'est aux pages appelantes de ne le monter qu'une fois `data` non nul.
 */

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { FeatureChatContextuel } from "@/api";
import { useChatContextuel } from "./useChatContextuel";
import Button from "@/components/Button";
import RichOutput from "@/components/RichOutput";

interface ChatContextuelPanelProps<T> {
  feature: FeatureChatContextuel;
  resultatActuel: T;
  onMiseAJour: (nouveauResultat: T) => void;
  dossierId?: number | null;
  /** Placeholder de la zone de saisie, adapté au vocabulaire de la page appelante. */
  placeholder?: string;
}

export default function ChatContextuelPanel<T>({
  feature,
  resultatActuel,
  onMiseAJour,
  dossierId,
  placeholder = "Ex. « Développe le deuxième argument », « rends le ton plus formel »…",
}: ChatContextuelPanelProps<T>) {
  const [ouvert, setOuvert] = useState(false);
  const [texte, setTexte] = useState("");
  const { messages, loading, envoyer, reinitialiser } = useChatContextuel(feature, resultatActuel, onMiseAJour, dossierId);
  const conteneurRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = conteneurRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  const soumettre = () => {
    const valeur = texte;
    setTexte("");
    void envoyer(valeur);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      soumettre();
    }
  };

  if (!ouvert) {
    return (
      <button
        type="button"
        onClick={() => setOuvert(true)}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-amethyst-400 hover:underline"
      >
        💬 Demander à l'agent
      </button>
    );
  }

  return (
    <div className="card space-y-3 p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-ivory">Demander à l'agent</p>
        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <button type="button" onClick={reinitialiser} className="text-xs text-muted hover:text-warmgray">
              Réinitialiser le fil
            </button>
          )}
          <button type="button" onClick={() => setOuvert(false)} className="text-xs text-muted hover:text-warmgray" aria-label="Replier">
            Replier
          </button>
        </div>
      </div>

      {messages.length > 0 && (
        <div ref={conteneurRef} className="max-h-64 space-y-3 overflow-y-auto rounded-md bg-surface-2/60 p-3">
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "text-right" : ""}>
              <div
                className={`inline-block max-w-[90%] rounded-md px-3 py-2 text-left text-sm ${
                  m.role === "user" ? "bg-amethyst-400/15 text-ivory" : "bg-surface text-ivory"
                }`}
              >
                {m.role === "assistant" ? <RichOutput texte={m.content} prose={false} className="text-sm" /> : m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-warmgray">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-gold-600/30 border-t-gold-500" aria-hidden="true" />
              L'agent réfléchit…
            </div>
          )}
        </div>
      )}

      <div className="flex items-end gap-2">
        <textarea
          className="input min-h-[44px] resize-none"
          rows={1}
          placeholder={placeholder}
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={loading}
        />
        <Button variant="primary" loading={loading} disabled={!texte.trim()} onClick={soumettre}>
          Envoyer
        </Button>
      </div>
    </div>
  );
}
