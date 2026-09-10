/**
 * TaskBar — barre de tâches : centre de navigation rapide, transversal à
 * l'espace actif (Avocat/Greffier), complémentaire de la Sidebar plutôt que
 * redondant avec elle (voir AUDIT_TASKBAR.md). Étape 1 du chantier "Barre
 * de tâches" -- seules les entrées qui pointent vers une fonctionnalité
 * RÉELLEMENT existante sont incluses ; Épinglés/Tâches/Notifications/
 * Versions rejoindront cette barre au fur et à mesure de leurs propres
 * étapes, jamais avant d'être fonctionnels (voir §14 de la demande :
 * "ne crée pas de données fictives pour simuler une fonctionnalité").
 */

import { useState } from "react";
import { NavLink } from "react-router-dom";
import RecentsPanel from "./RecentsPanel";

const RACCOURCIS = [
  { path: "/app", icone: "🏠", label: "Accueil", fin: true },
  { path: "/app/chemise/dossiers", icone: "📁", label: "Mes dossiers", fin: false },
  { path: "/app/chat", icone: "🤖", label: "Assistant", fin: false },
  { path: "/app/greffier/recherche", icone: "🔍", label: "Recherche", fin: false },
];

export default function TaskBar() {
  const [recentsOuvert, setRecentsOuvert] = useState(false);

  return (
    <div className="flex items-center gap-1 border-b border-gold-600/10 bg-surface/30 px-4 py-1.5">
      {/* Le scroll horizontal (petits écrans) reste isolé à cette liste --
          overflow-x-auto sur la barre entière forcerait implicitement
          overflow-y en "auto" et rognerait le menu déroulant "Récents"
          qui dépasse en dessous. */}
      <div className="flex min-w-0 items-center gap-1 overflow-x-auto">
        {RACCOURCIS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.fin}
            className={({ isActive }) =>
              `shrink-0 whitespace-nowrap rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                isActive ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:bg-surface-2 hover:text-ivory"
              }`
            }
          >
            {item.icone} {item.label}
          </NavLink>
        ))}
      </div>

      <div className="relative ml-auto shrink-0">
        <button
          onClick={() => setRecentsOuvert((v) => !v)}
          className={`whitespace-nowrap rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
            recentsOuvert ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:bg-surface-2 hover:text-ivory"
          }`}
          aria-haspopup="true"
          aria-expanded={recentsOuvert}
        >
          🕘 Récents
        </button>
        {recentsOuvert && <RecentsPanel onFermer={() => setRecentsOuvert(false)} />}
      </div>
    </div>
  );
}
