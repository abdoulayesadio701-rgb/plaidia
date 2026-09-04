/**
 * Modal — fenêtre modale générique (fond obscurci, fermeture sur Échap et
 * clic hors-cadre), base de tout dialogue de saisie de l'app — équivalent
 * web des `tk.Toplevel` de gui.py (DialogueNouveauDossier, etc.).
 *
 * Traitement : filet dégradé or→améthyste en tête de carte (signature
 * visuelle des dialogues, voir DESIGN.md), entrée en fondu + léger
 * agrandissement plutôt qu'une apparition sèche — respecte
 * prefers-reduced-motion.
 *
 * `icone` est rendue TELLE QUELLE, sans badge automatique — les dialogues
 * simples passent une icône déjà enveloppée dans leur propre petit badge
 * (voir NouveauDossierModal si besoin) ; les dialogues à traitement bespoke
 * (TexteLongModal et son sceau de cire) passent un graphisme déjà complet.
 * `kicker` est le petit intitulé au-dessus du titre (ex. "Dépôt de pièce").
 * `titreDefile` fait défiler le titre en boucle (façon mot-marque du nav,
 * voir TopBar.tsx) au lieu de l'afficher statique — à réserver aux
 * dialogues qui le méritent, pas un défaut pour toutes les modales.
 */

import { useEffect, type ReactNode } from "react";

interface ModalProps {
  titre: string;
  onFermer: () => void;
  children: ReactNode;
  largeurMax?: string;
  icone?: ReactNode;
  kicker?: string;
  titreDefile?: boolean;
}

export default function Modal({ titre, onFermer, children, largeurMax = "max-w-md", icone, kicker, titreDefile = false }: ModalProps) {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onFermer();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onFermer]);

  return (
    <div
      className="modal-scrim fixed inset-0 z-40 flex items-center justify-center bg-void/80 p-4 backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onFermer();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-titre"
    >
      <div
        className={`modal-pop card relative w-full overflow-hidden ${largeurMax} max-h-[85vh] overflow-y-auto`}
      >
        <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-gold-500 to-amethyst-400" aria-hidden="true" />

        <div className="mb-5 flex items-start gap-4">
          {icone && <div className="shrink-0">{icone}</div>}
          <div className={`min-w-0 flex-1 ${icone ? "pt-1.5" : ""}`}>
            {kicker && <p className="kicker">{kicker}</p>}
            {titreDefile ? (
              <div className="marquee-mini mt-0.5">
                <div className="marquee-mini-track">
                  <h2 id="modal-titre" className="font-serif text-h3 font-semibold text-gold-500">
                    {titre}
                  </h2>
                  <span className="text-amethyst-400" aria-hidden="true">
                    ◆
                  </span>
                  <h2 className="font-serif text-h3 font-semibold text-gold-500" aria-hidden="true">
                    {titre}
                  </h2>
                  <span className="text-amethyst-400" aria-hidden="true">
                    ◆
                  </span>
                </div>
              </div>
            ) : (
              <h2 id="modal-titre" className="font-serif text-h3 font-semibold text-gold-500">
                {titre}
              </h2>
            )}
          </div>
          <button
            onClick={onFermer}
            className={`shrink-0 rounded-md p-1 text-warmgray hover:bg-surface-2 hover:text-ivory ${icone ? "mt-1.5" : ""}`}
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
