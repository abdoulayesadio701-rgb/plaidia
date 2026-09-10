/**
 * ChoixImportModal — quand le champ visé par un import de fichier contient
 * déjà du texte, demande explicitement à l'utilisateur s'il faut remplacer
 * ce texte ou ajouter le contenu importé à la suite (voir useImportTexte).
 * Jamais affichée si le champ était vide -- l'import s'y injecte alors
 * directement, sans interruption inutile.
 */

import Modal from "./Modal";
import Button from "./Button";

interface ChoixImportModalProps {
  noms: string[];
  onChoisir: (mode: "remplacer" | "ajouter" | "annuler") => void;
}

export default function ChoixImportModal({ noms, onChoisir }: ChoixImportModalProps) {
  const sujet = noms.length > 1 ? `ces ${noms.length} fichiers (${noms.join(", ")})` : `« ${noms[0]} »`;
  return (
    <Modal titre="Du texte est déjà présent" onFermer={() => onChoisir("annuler")}>
      <div className="space-y-4">
        <p className="text-sm text-warmgray">
          Ce champ contient déjà du texte. Que faire du contenu extrait de {sujet} ?
        </p>
        <div className="flex flex-wrap justify-end gap-3">
          <Button type="button" variant="ghost" onClick={() => onChoisir("annuler")}>
            Annuler
          </Button>
          <Button type="button" variant="secondary" onClick={() => onChoisir("ajouter")}>
            Ajouter à la suite
          </Button>
          <Button type="button" variant="primary" onClick={() => onChoisir("remplacer")}>
            Remplacer
          </Button>
        </div>
      </div>
    </Modal>
  );
}
