/**
 * RecentsPanel — liste déroulante des dernières pages consultées (voir
 * config/recents.ts, hooks/useSuivreRecents.ts). Cliquer une entrée
 * resélectionne le dossier qui était actif à ce moment-là (s'il existe
 * toujours) puis navigue vers la page -- reprendre le travail là où on
 * l'a laissé, sans dupliquer aucune donnée.
 */

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ecouterChangementsRecents, listerRecents, viderRecents, type ElementRecent } from "@/config/recents";
import { navKey } from "@/config/navigation";
import { useAppStore } from "@/store/useAppStore";

function formaterDate(iso: string, langue: string): string {
  const date = new Date(iso);
  const maintenant = new Date();
  const memeJour = date.toDateString() === maintenant.toDateString();
  const locale = langue === "en" ? "en-GB" : "fr-FR";
  if (memeJour) return date.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
  return date.toLocaleDateString(locale, { day: "2-digit", month: "short" });
}

interface RecentsPanelProps {
  onFermer: () => void;
}

/** "/" et "/parametres" sont hors de navigation.ts (voir
 * useSuivreRecents.ts::LIBELLES_HORS_NAVIGATION) -- clés dédiées plutôt que
 * navKey(), qui ne sait résoudre que des chemins de navigation.ts. */
function cleLabelRecent(path: string): string {
  if (path === "/") return "nav.accueil";
  if (path === "/parametres") return "nav.parametresPage";
  return navKey(path);
}

export default function RecentsPanel({ onFermer }: RecentsPanelProps) {
  const { t, i18n } = useTranslation();
  const [elements, setElements] = useState<ElementRecent[]>(() => listerRecents());
  const conteneurRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const dossiers = useAppStore((s) => s.dossiers);
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);

  useEffect(() => {
    const arreterEcoute = ecouterChangementsRecents(() => setElements(listerRecents()));
    return arreterEcoute;
  }, []);

  useEffect(() => {
    const onClickDehors = (e: MouseEvent) => {
      if (conteneurRef.current && !conteneurRef.current.contains(e.target as Node)) onFermer();
    };
    document.addEventListener("mousedown", onClickDehors);
    return () => document.removeEventListener("mousedown", onClickDehors);
  }, [onFermer]);

  const ouvrir = (element: ElementRecent) => {
    // Ne resélectionne le dossier que s'il existe encore -- un dossier
    // supprimé depuis ne doit jamais bloquer la navigation vers la page.
    if (element.dossierId !== null && dossiers.some((d) => d.id === element.dossierId)) {
      selectionnerDossier(element.dossierId);
    }
    navigate(`/app${element.path}`);
    onFermer();
  };

  return (
    <div ref={conteneurRef} className="absolute right-0 top-full z-30 mt-2 w-80 rounded-md border border-gold-600/25 bg-surface-2 shadow-card">
      <div className="flex items-center justify-between border-b border-gold-600/15 px-3 py-2">
        <p className="text-xs font-medium text-warmgray">{t("recentsPanel.titre")}</p>
        {elements.length > 0 && (
          <button onClick={() => viderRecents()} className="text-xs text-muted hover:text-warmgray">
            {t("recentsPanel.vider")}
          </button>
        )}
      </div>
      <ul className="max-h-80 overflow-y-auto p-1">
        {elements.map((el) => (
          <li key={el.id}>
            <button onClick={() => ouvrir(el)} className="block w-full rounded-md px-2.5 py-2 text-left text-sm text-ivory transition-colors hover:bg-surface">
              <span className="block truncate">{t(cleLabelRecent(el.path), el.label)}</span>
              <span className="mt-0.5 flex items-center justify-between text-xs text-warmgray">
                <span className="truncate">{el.dossierNom ?? t("recentsPanel.sansDossier")}</span>
                <span className="shrink-0 tabular-nums">{formaterDate(el.date, i18n.language)}</span>
              </span>
            </button>
          </li>
        ))}
        {elements.length === 0 && <li className="px-2.5 py-3 text-sm text-warmgray">{t("recentsPanel.vide")}</li>}
      </ul>
    </div>
  );
}
