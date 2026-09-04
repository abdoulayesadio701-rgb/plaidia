/**
 * ConfirmerSuppressionModal — confirmation forte pour une suppression
 * irréversible : le bouton ne s'active que si l'utilisateur retape le nom
 * exact de l'élément à supprimer (même logique que GitHub pour la
 * suppression d'un dépôt). Réservé aux suppressions qui n'ont pas de
 * garde-fou côté backend (ex. dossier : DELETE cascade sur ses analyses).
 */

import { useState, type ReactNode } from "react";
import Modal from "./Modal";
import Button from "./Button";

interface ConfirmerSuppressionModalProps {
  titre: string;
  /** Texte exact que l'utilisateur doit retaper (ex. le nom du dossier). */
  texteConfirmation: string;
  description?: ReactNode;
  onFermer: () => void;
  onConfirmer: () => void | Promise<void>;
  enCours?: boolean;
}

export default function ConfirmerSuppressionModal({
  titre,
  texteConfirmation,
  description,
  onFermer,
  onConfirmer,
  enCours = false,
}: ConfirmerSuppressionModalProps) {
  const [saisie, setSaisie] = useState("");
  const correspond = saisie.trim() === texteConfirmation && texteConfirmation.trim() !== "";

  return (
    <Modal
      titre={titre}
      onFermer={onFermer}
      icone={
        <span className="flex h-11 w-11 items-center justify-center rounded-full border border-risk-high/40 bg-risk-high/10 text-xl text-risk-high">
          ⚠
        </span>
      }
    >
      <div className="space-y-4">
        {description && <div className="text-sm text-warmgray">{description}</div>}
        <div>
          <label htmlFor="confirmation-suppression" className="mb-1.5 block text-sm text-warmgray">
            Tapez <span className="font-mono text-ivory">{texteConfirmation}</span> pour confirmer
          </label>
          <input
            id="confirmation-suppression"
            className="input"
            value={saisie}
            onChange={(e) => setSaisie(e.target.value)}
            autoFocus
            autoComplete="off"
          />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onFermer}>
            Annuler
          </Button>
          <Button
            type="button"
            variant="primary"
            className="!bg-risk-high !text-ivory hover:!bg-risk-high/85 hover:!shadow-none"
            disabled={!correspond}
            loading={enCours}
            onClick={() => void onConfirmer()}
          >
            Supprimer définitivement
          </Button>
        </div>
      </div>
    </Modal>
  );
}
