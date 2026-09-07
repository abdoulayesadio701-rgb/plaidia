/**
 * ConfirmerModal — confirmation simple (pas de ressaisie de nom, contrairement
 * à ConfirmerSuppressionModal) : pour une action qui mérite un temps d'arrêt
 * sans être une suppression irréversible — ex. valider en bloc tout un
 * import (GererCorpusPage). Un clic sur "Annuler" ou Échap referme sans
 * rien faire.
 */

import Modal from "./Modal";
import Button from "./Button";

interface ConfirmerModalProps {
  titre: string;
  description: React.ReactNode;
  texteBouton?: string;
  onFermer: () => void;
  onConfirmer: () => void | Promise<void>;
  enCours?: boolean;
}

export default function ConfirmerModal({
  titre,
  description,
  texteBouton = "Confirmer",
  onFermer,
  onConfirmer,
  enCours = false,
}: ConfirmerModalProps) {
  return (
    <Modal titre={titre} onFermer={onFermer}>
      <div className="space-y-4">
        <div className="text-sm text-warmgray">{description}</div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onFermer}>
            Annuler
          </Button>
          <Button type="button" variant="primary" loading={enCours} onClick={() => void onConfirmer()}>
            {texteBouton}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
