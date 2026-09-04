/**
 * TexteLongModal — grande zone de saisie pour coller un texte long
 * (réquisitoire, conclusions, jugement...), équivalent web de
 * DialogueTexteLong (gui.py). Réutilisable partout où un futur formulaire
 * a besoin de la même mécanique (analyse de conclusions, etc.).
 *
 * Choix délibéré, différent de gui.py::_coller_texte_long_chat : le texte
 * validé est INSÉRÉ dans la zone de saisie appelante plutôt qu'envoyé
 * immédiatement — envoyer un réquisitoire entier sans pouvoir le relire
 * ni y ajouter une consigne serait trop peu réversible pour un outil
 * professionnel.
 *
 * Traitement "dépôt de pièce" (voir globals.css §Parchemin) : la zone de
 * texte devient un ilot de parchemin clair, scellé d'un cachet de cire
 * améthyste qui se craquelle à l'ouverture — seule exception délibérée à
 * la palette sombre (au même titre que le marqueur "À VÉRIFIER"), pensée
 * pour ce geste précis : déposer une pièce dans le dossier.
 */

import { useEffect, useState, type KeyboardEvent } from "react";
import { useAppStore } from "@/store/useAppStore";
import Modal from "./Modal";
import Button from "./Button";
import sceauJusticePhoto from "@/assets/sceau-justice.jpg";

interface TexteLongModalProps {
  titre: string;
  consigne: string;
  onFermer: () => void;
  onValider: (texte: string) => void;
}

function IconePresserPapiers() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <rect x={7} y={5} width={10} height={15} rx={1.5} />
      <path d="M9.5 5V4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1" />
      <path d="M9.5 10.5l2 2 3.5-4" />
    </svg>
  );
}

function IconePlume() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 20l4-1 10-10a2 2 0 0 0-3-3L5 16l-1 4z" />
    </svg>
  );
}

/** Le cachet — une vraie photo de la balance (voir DESIGN.md §1.8),
 * assombrie et cerclée d'or plutôt que la maquette en dégradé améthyste
 * de la première itération : "couleurs noir + photo du symbole", retour
 * direct de l'utilisateur. La craquelure reste dorée, façon kintsugi. */
function SceauDeCire() {
  return (
    <div className="wax-seal" aria-hidden="true">
      <div className="seal-photo-frame">
        <img src={sceauJusticePhoto} alt="" className="seal-photo" />
        <div className="seal-vignette" />
        <svg viewBox="0 0 52 52" className="seal-crack-overlay">
          <path className="seal-crack" d="M6 22 Q17 27 26 24 T46 20" stroke="#E6C76A" strokeWidth={1.4} fill="none" strokeLinecap="round" />
        </svg>
      </div>
    </div>
  );
}

export default function TexteLongModal({ titre, consigne, onFermer, onValider }: TexteLongModalProps) {
  const [texte, setTexte] = useState("");
  const [pulse, setPulse] = useState(false);
  const pousserToast = useAppStore((s) => s.pousserToast);

  // Petit accent améthyste sur le compteur à chaque frappe, retombe aussitôt
  // -- feedback discret que "le texte est bien pris en compte". Ignore le
  // montage initial (texte encore vide) pour ne pas flasher à l'ouverture.
  useEffect(() => {
    if (texte === "") {
      setPulse(false);
      return;
    }
    setPulse(true);
    const t = setTimeout(() => setPulse(false), 350);
    return () => clearTimeout(t);
  }, [texte]);

  const valider = () => {
    if (!texte.trim()) return;
    onValider(texte.trim());
    onFermer();
  };

  const collerDepuisPressePapiers = async () => {
    try {
      const contenu = (await navigator.clipboard.readText()).trim();
      if (contenu) setTexte((precedent) => (precedent ? `${precedent}\n${contenu}` : contenu));
    } catch {
      pousserToast("error", "Lecture du presse-papiers refusée par le navigateur — collez manuellement (Ctrl/Cmd+V) dans la zone.");
    }
  };

  const onKeyDownZone = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      valider();
    }
  };

  return (
    <Modal titre={titre} onFermer={onFermer} largeurMax="max-w-2xl" icone={<SceauDeCire />} kicker="Dépôt de pièce" titreDefile>
      <p className="mb-4 text-sm leading-relaxed text-warmgray">{consigne}</p>

      <div className="intake-toolbar">
        <button type="button" onClick={() => void collerDepuisPressePapiers()} className="paste-btn">
          <IconePresserPapiers />
          Coller depuis le presse-papiers
        </button>
        <span className={`char-counter ${pulse ? "pulse" : ""}`}>
          <IconePlume />
          {texte.length.toLocaleString("fr-FR")} caractère{texte.length > 1 ? "s" : ""}
        </span>
      </div>

      <div className="parchment-wrap">
        <div className="parchment-fold" />
        <textarea
          autoFocus
          className="parchment-textarea"
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          onKeyDown={onKeyDownZone}
        />
        {texte === "" && (
          <div className="parchment-watermark">
            <p>
              Déposez le texte ici,
              <br />
              comme une pièce au dossier.
            </p>
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="hidden text-xs text-muted sm:block">
          <kbd className="rounded border border-gold-600/30 px-1.5 py-0.5 font-mono">Ctrl</kbd>
          {" + "}
          <kbd className="rounded border border-gold-600/30 px-1.5 py-0.5 font-mono">Entrée</kbd> pour insérer
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={onFermer}>
            Annuler
          </Button>
          <Button variant="primary" disabled={!texte.trim()} onClick={valider}>
            Insérer dans la conversation
          </Button>
        </div>
      </div>
    </Modal>
  );
}
