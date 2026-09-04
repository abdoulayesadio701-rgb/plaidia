/**
 * DossierSelector — combo dossier actif : recherche dans les dossiers déjà
 * chargés (useAppStore.dossiers) + raccourci de création rapide en pied de
 * liste. La création complète (avec faits) reste sur le bouton "Nouveau
 * dossier" à côté, via NouveauDossierModal.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { useAppStore, useDossierActif } from "@/store/useAppStore";

interface DossierSelectorProps {
  onDemanderCreation: (nomPrerempli?: string) => void;
}

export default function DossierSelector({ onDemanderCreation }: DossierSelectorProps) {
  const [ouvert, setOuvert] = useState(false);
  const [recherche, setRecherche] = useState("");
  const conteneurRef = useRef<HTMLDivElement>(null);

  const dossiers = useAppStore((s) => s.dossiers);
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const dossierActif = useDossierActif();

  useEffect(() => {
    if (!ouvert) return;
    const onClickDehors = (e: MouseEvent) => {
      if (conteneurRef.current && !conteneurRef.current.contains(e.target as Node)) setOuvert(false);
    };
    document.addEventListener("mousedown", onClickDehors);
    return () => document.removeEventListener("mousedown", onClickDehors);
  }, [ouvert]);

  const resultats = useMemo(() => {
    const terme = recherche.trim().toLowerCase();
    if (!terme) return dossiers;
    return dossiers.filter((d) => d.nom.toLowerCase().includes(terme) || (d.domaine ?? "").toLowerCase().includes(terme));
  }, [dossiers, recherche]);

  return (
    <div ref={conteneurRef} className="relative">
      <button
        onClick={() => setOuvert((o) => !o)}
        className="input flex w-64 items-center justify-between gap-2 text-left"
        aria-haspopup="listbox"
        aria-expanded={ouvert}
      >
        <span className={`truncate text-sm ${dossierActif ? "text-ivory" : "text-muted"}`}>
          {dossierActif ? dossierActif.nom : "Aucun dossier sélectionné"}
        </span>
        <span className="shrink-0 text-warmgray">▾</span>
      </button>

      {ouvert && (
        <div className="absolute left-0 top-full z-30 mt-2 w-80 rounded-md border border-gold-600/25 bg-surface-2 shadow-card">
          <div className="p-2">
            <input
              autoFocus
              className="input"
              placeholder="Rechercher un dossier…"
              aria-label="Rechercher un dossier"
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
            />
          </div>
          <ul className="max-h-64 overflow-y-auto px-1 pb-1" role="listbox">
            {resultats.map((d) => (
              <li key={d.id}>
                <button
                  onClick={() => {
                    selectionnerDossier(d.id);
                    setOuvert(false);
                    setRecherche("");
                  }}
                  className={`block w-full rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-surface ${
                    d.id === dossierActif?.id ? "text-amethyst-400" : "text-ivory"
                  }`}
                >
                  <span className="block truncate">{d.nom}</span>
                  {d.domaine && <span className="block truncate text-xs text-warmgray">{d.domaine}</span>}
                </button>
              </li>
            ))}
            {resultats.length === 0 && (
              <li className="px-2.5 py-2 text-sm text-warmgray">Aucun dossier ne correspond.</li>
            )}
          </ul>
          <div className="border-t border-gold-600/15 p-1">
            <button
              onClick={() => {
                setOuvert(false);
                onDemanderCreation(recherche.trim() || undefined);
              }}
              className="block w-full rounded-md px-2.5 py-2 text-left text-sm text-gold-500 transition-colors hover:bg-surface"
            >
              ＋ Créer{recherche.trim() ? ` « ${recherche.trim()} »` : " un nouveau dossier"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
