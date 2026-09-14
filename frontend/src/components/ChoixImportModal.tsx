/**
 * ChoixImportModal — quand le champ visé par un import de fichier contient
 * déjà du texte, demande explicitement à l'utilisateur s'il faut remplacer
 * ce texte ou ajouter le contenu importé à la suite (voir useImportTexte).
 * Jamais affichée si le champ était vide -- l'import s'y injecte alors
 * directement, sans interruption inutile.
 */

import { useTranslation } from "react-i18next";
import Modal from "./Modal";
import Button from "./Button";

interface ChoixImportModalProps {
  noms: string[];
  onChoisir: (mode: "remplacer" | "ajouter" | "annuler") => void;
}

export default function ChoixImportModal({ noms, onChoisir }: ChoixImportModalProps) {
  const { t } = useTranslation();
  const sujet = noms.length > 1 ? t("choixImportModal.sujetPluriel", { count: noms.length, noms: noms.join(", ") }) : t("choixImportModal.sujetSingulier", { nom: noms[0] });
  return (
    <Modal titre={t("choixImportModal.titre")} onFermer={() => onChoisir("annuler")}>
      <div className="space-y-4">
        <p className="text-sm text-warmgray">{t("choixImportModal.question", { sujet })}</p>
        <div className="flex flex-wrap justify-end gap-3">
          <Button type="button" variant="ghost" onClick={() => onChoisir("annuler")}>
            {t("commun.annuler")}
          </Button>
          <Button type="button" variant="secondary" onClick={() => onChoisir("ajouter")}>
            {t("choixImportModal.ajouter")}
          </Button>
          <Button type="button" variant="primary" onClick={() => onChoisir("remplacer")}>
            {t("choixImportModal.remplacer")}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
