/**
 * PinButton — bouton Épingler / Désépingler réutilisable (voir
 * AUDIT_TASKBAR.md, étape 2). Épingler crée uniquement un pointeur
 * (type + reference_id) vers l'élément original -- jamais une copie de
 * son contenu (voir db.py::epingler et son commentaire).
 */

import { useAppStore, useIdEpingle } from "@/store/useAppStore";
import type { TypeEpingle } from "@/api";

interface PinButtonProps {
  type: TypeEpingle;
  referenceId: number;
  libelle: string;
  dossierId?: number | null;
  /** Empêche la navigation du parent (ex. une carte cliquable entière) quand le bouton est dans une zone déjà cliquable. */
  arreterPropagation?: boolean;
  className?: string;
}

export default function PinButton({ type, referenceId, libelle, dossierId, arreterPropagation = false, className = "" }: PinButtonProps) {
  const idEpingle = useIdEpingle(type, referenceId);
  const epinglerElement = useAppStore((s) => s.epinglerElement);
  const desepinglerElement = useAppStore((s) => s.desepinglerElement);
  const estEpingle = idEpingle !== null;

  const onClick = (e: React.MouseEvent) => {
    if (arreterPropagation) e.stopPropagation();
    if (estEpingle) {
      void desepinglerElement(idEpingle);
    } else {
      void epinglerElement(type, referenceId, libelle, dossierId);
    }
  };

  return (
    <button
      onClick={onClick}
      className={`rounded-md px-2 py-1 text-xs transition-colors ${
        estEpingle ? "text-amethyst-400 hover:bg-amethyst-400/10" : "text-warmgray hover:bg-surface-2 hover:text-ivory"
      } ${className}`}
      title={estEpingle ? "Désépingler" : "Épingler"}
      aria-pressed={estEpingle}
    >
      {estEpingle ? "📍 Épinglé" : "📌 Épingler"}
    </button>
  );
}
