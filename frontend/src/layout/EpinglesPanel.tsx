/**
 * EpinglesPanel — liste déroulante des éléments épinglés (voir
 * AUDIT_TASKBAR.md, étape 2 ; store useAppStore::epingles). Cliquer une
 * entrée resélectionne le dossier associé puis navigue vers l'endroit où
 * la retrouver -- un pin n'est qu'un pointeur, jamais une copie, donc
 * "l'ouvrir" veut toujours dire "aller voir l'original".
 */

import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import type { ElementEpingle } from "@/api";
import { useAppStore } from "@/store/useAppStore";

interface EpinglesPanelProps {
  onFermer: () => void;
}

const LIBELLE_TYPE: Record<string, string> = {
  dossier: "Dossier",
  analyse: "Analyse enregistrée",
  document_genere: "Document généré",
  conversation: "Conversation",
};

export default function EpinglesPanel({ onFermer }: EpinglesPanelProps) {
  const conteneurRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const epingles = useAppStore((s) => s.epingles);
  const desepinglerElement = useAppStore((s) => s.desepinglerElement);
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const dossiers = useAppStore((s) => s.dossiers);

  useEffect(() => {
    const onClickDehors = (e: MouseEvent) => {
      if (conteneurRef.current && !conteneurRef.current.contains(e.target as Node)) onFermer();
    };
    document.addEventListener("mousedown", onClickDehors);
    return () => document.removeEventListener("mousedown", onClickDehors);
  }, [onFermer]);

  const ouvrir = (el: ElementEpingle) => {
    const dossierCible = el.type === "dossier" ? el.reference_id : el.dossier_id;
    if (dossierCible != null && dossiers.some((d) => d.id === dossierCible)) {
      selectionnerDossier(dossierCible);
    }
    if (el.type === "dossier") navigate("/app/chemise/dossiers");
    else if (el.type === "analyse") navigate("/app/chemise/historique");
    else if (el.type === "conversation") navigate(`/app/chat?conversation_id=${el.reference_id}`);
    else if (el.cible_feature === "plan") navigate(`/app/arsenal/plan?document_id=${el.reference_id}`);
    else if (el.cible_feature === "simulateur") navigate(`/app/arsenal/simulateur?document_id=${el.reference_id}`);
    else if (el.cible_feature === "jurisprudence_consultation") navigate(`/app/grimoire/jurisprudence?document_id=${el.reference_id}`);
    else navigate(`/app/chemise/historique`);
    onFermer();
  };

  return (
    <div ref={conteneurRef} className="absolute right-0 top-full z-30 mt-2 w-80 rounded-md border border-gold-600/25 bg-surface-2 shadow-card">
      <div className="border-b border-gold-600/15 px-3 py-2">
        <p className="text-xs font-medium text-warmgray">Épinglés</p>
      </div>
      <ul className="max-h-80 overflow-y-auto p-1">
        {epingles.map((el) => (
          <li key={el.id} className="flex items-center gap-1">
            <button onClick={() => ouvrir(el)} className="min-w-0 flex-1 rounded-md px-2.5 py-2 text-left text-sm text-ivory transition-colors hover:bg-surface">
              <span className="block truncate">{el.cible_titre ?? el.libelle}</span>
              <span className="text-xs text-warmgray">{LIBELLE_TYPE[el.type] ?? el.type}{el.dossier_id != null ? ` · dossier #${el.dossier_id}` : ""}</span>
            </button>
            <button
              onClick={() => void desepinglerElement(el.id)}
              className="shrink-0 rounded-md px-2 py-1 text-xs text-muted hover:text-risk-high"
              title="Désépingler"
              aria-label={`Désépingler ${el.libelle}`}
            >
              ✕
            </button>
          </li>
        ))}
        {epingles.length === 0 && <li className="px-2.5 py-3 text-sm text-warmgray">Rien d'épinglé pour l'instant.</li>}
      </ul>
    </div>
  );
}
