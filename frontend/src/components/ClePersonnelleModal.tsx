/**
 * ClePersonnelleModal — enveloppe modale de ClePersonnelleForm, pour l'accès
 * rapide depuis le bandeau du mode démo (DemoBanner). Le même formulaire est
 * aussi accessible sans modale, en continu, depuis ParametresPage.
 */

import { useTranslation } from "react-i18next";
import Modal from "./Modal";
import ClePersonnelleForm from "./ClePersonnelleForm";

interface ClePersonnelleModalProps {
  onFermer: () => void;
}

export default function ClePersonnelleModal({ onFermer }: ClePersonnelleModalProps) {
  const { t } = useTranslation();
  return (
    <Modal titre={t("clePersonnelle.modalTitre")} onFermer={onFermer} kicker={t("clePersonnelle.modalKicker")}>
      <ClePersonnelleForm onValide={onFermer} />
    </Modal>
  );
}
