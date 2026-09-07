/**
 * ClePersonnelleModal — enveloppe modale de ClePersonnelleForm, pour l'accès
 * rapide depuis le bandeau du mode démo (DemoBanner). Le même formulaire est
 * aussi accessible sans modale, en continu, depuis ParametresPage.
 */

import Modal from "./Modal";
import ClePersonnelleForm from "./ClePersonnelleForm";

interface ClePersonnelleModalProps {
  onFermer: () => void;
}

export default function ClePersonnelleModal({ onFermer }: ClePersonnelleModalProps) {
  return (
    <Modal titre="Ma propre clé Anthropic" onFermer={onFermer} kicker="Sortir du mode démo">
      <ClePersonnelleForm onValide={onFermer} />
    </Modal>
  );
}
