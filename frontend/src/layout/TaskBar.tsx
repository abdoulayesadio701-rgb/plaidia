/**
 * TaskBar — barre de tâches : centre de navigation rapide, transversal à
 * l'espace actif (Avocat/Greffier), complémentaire de la Sidebar plutôt que
 * redondant avec elle (voir AUDIT_TASKBAR.md). Étapes 1 à 3 du chantier
 * "barre de tâches" -- Tâches/Notifications/Versions rejoindront cette
 * barre au fur et à mesure de leurs propres étapes, jamais avant d'être
 * fonctionnels (voir §14 de la demande : "ne crée pas de données
 * fictives pour simuler une fonctionnalité"). "Recherche" ouvre la vraie
 * palette de recherche globale (RechercheGlobaleModal) plutôt que de
 * naviguer vers une page dédiée -- même raccourci clavier Ctrl/Cmd+K.
 */

import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAppStore } from "@/store/useAppStore";
import RecentsPanel from "./RecentsPanel";
import EpinglesPanel from "./EpinglesPanel";
import SelecteurLangue from "@/components/SelecteurLangue";

type PanneauOuvert = "recents" | "epingles" | null;

export default function TaskBar() {
  const { t } = useTranslation();
  const [panneauOuvert, setPanneauOuvert] = useState<PanneauOuvert>(null);
  const nombreEpingles = useAppStore((s) => s.epingles.length);
  const ouvrirRechercheGlobale = useAppStore((s) => s.ouvrirRechercheGlobale);

  const RACCOURCIS = [
    { path: "/app", icone: "🏠", label: t("taskBar.accueil"), fin: true },
    { path: "/app/chemise/dossiers", icone: "📁", label: t("taskBar.mesDossiers"), fin: false },
    { path: "/app/chat", icone: "🤖", label: t("taskBar.assistant"), fin: false },
  ];

  const basculer = (panneau: PanneauOuvert) => setPanneauOuvert((actuel) => (actuel === panneau ? null : panneau));

  return (
    <div className="flex items-center gap-1 border-b border-gold-600/10 bg-surface/30 px-4 py-1.5">
      {/* Le scroll horizontal (petits écrans) reste isolé à cette liste --
          overflow-x-auto sur la barre entière forcerait implicitement
          overflow-y en "auto" et rognerait les menus déroulants qui
          dépassent en dessous. */}
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

      <div className="ml-auto flex shrink-0 items-center gap-1">
        <button
          onClick={ouvrirRechercheGlobale}
          className="whitespace-nowrap rounded-md px-2.5 py-1 text-xs font-medium text-warmgray transition-colors hover:bg-surface-2 hover:text-ivory"
          title={t("taskBar.rechercheGlobale")}
        >
          🔍 {t("taskBar.recherche")} <span className="text-muted">Ctrl K</span>
        </button>

        <div className="relative">
          <button
            onClick={() => basculer("epingles")}
            className={`whitespace-nowrap rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              panneauOuvert === "epingles" ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:bg-surface-2 hover:text-ivory"
            }`}
            aria-haspopup="true"
            aria-expanded={panneauOuvert === "epingles"}
          >
            📌 {t("taskBar.epingles")}{nombreEpingles > 0 && ` (${nombreEpingles})`}
          </button>
          {panneauOuvert === "epingles" && <EpinglesPanel onFermer={() => setPanneauOuvert(null)} />}
        </div>

        <div className="relative">
          <button
            onClick={() => basculer("recents")}
            className={`whitespace-nowrap rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              panneauOuvert === "recents" ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:bg-surface-2 hover:text-ivory"
            }`}
            aria-haspopup="true"
            aria-expanded={panneauOuvert === "recents"}
          >
            🕘 {t("taskBar.recents")}
          </button>
          {panneauOuvert === "recents" && <RecentsPanel onFermer={() => setPanneauOuvert(null)} />}
        </div>

        <SelecteurLangue />
      </div>
    </div>
  );
}
