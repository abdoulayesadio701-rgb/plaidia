/**
 * Accordion — un seul panneau ouvert à la fois, sur la carcasse .card.
 * Utilisé pour l'historique des analyses d'un dossier (La Chemise) ; assez
 * générique pour être réutilisé partout où une liste de blocs doit rester
 * compacte par défaut.
 */

import { useState, type ReactNode } from "react";

export interface AccordionItem {
  id: string | number;
  header: ReactNode;
  content: ReactNode;
}

interface AccordionProps {
  items: AccordionItem[];
  /** Id ouvert par défaut (ex. l'analyse la plus récente). */
  ouvertParDefaut?: string | number | null;
}

export default function Accordion({ items, ouvertParDefaut = null }: AccordionProps) {
  const [ouvertId, setOuvertId] = useState<string | number | null>(ouvertParDefaut);

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const ouvert = ouvertId === item.id;
        return (
          <div key={item.id} className="card overflow-hidden p-0">
            <button
              type="button"
              onClick={() => setOuvertId(ouvert ? null : item.id)}
              className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition-colors hover:bg-surface-2"
              aria-expanded={ouvert}
            >
              <div className="min-w-0 flex-1">{item.header}</div>
              <span
                className={`shrink-0 text-warmgray transition-transform duration-200 ${ouvert ? "rotate-180" : ""}`}
                aria-hidden="true"
              >
                ▾
              </span>
            </button>
            {ouvert && <div className="animate-[rise_0.2s_ease] space-y-4 border-t border-gold-600/15 px-5 py-5">{item.content}</div>}
          </div>
        );
      })}
    </div>
  );
}
