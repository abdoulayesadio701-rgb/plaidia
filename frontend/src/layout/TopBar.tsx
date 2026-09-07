/**
 * TopBar — bandeau du haut : logo, sélecteur de dossier actif, indicateur
 * de juridiction, bouton "Nouveau dossier". Reprend le bandeau de gui.py
 * (self.combo_dossiers, self.combo_juridiction, bouton "＋ Nouveau dossier").
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useAppStore } from "@/store/useAppStore";
import Logo from "@/components/Logo";
import Button from "@/components/Button";
import FullscreenToggle from "@/components/FullscreenToggle";
import NouveauDossierModal from "@/components/NouveauDossierModal";
import DossierSelector from "./DossierSelector";

export default function TopBar() {
  const [modalOuvert, setModalOuvert] = useState(false);
  const [nomPrerempli, setNomPrerempli] = useState<string | undefined>(undefined);

  const juridictionActive = useAppStore((s) => s.juridictionActive);
  const definirJuridictionActive = useAppStore((s) => s.definirJuridictionActive);
  // Chargée une fois au montage de AppLayout (et rafraîchie après toute
  // validation dans Le Grimoire) -- voir useAppStore::chargerSourcesJuridictions.
  const sources = useAppStore((s) => s.sourcesJuridictions);

  const ouvrirCreation = (nom?: string) => {
    setNomPrerempli(nom);
    setModalOuvert(true);
  };

  return (
    <>
      <header className="flex flex-wrap items-center gap-4 border-b border-gold-600/15 bg-surface/80 px-4 py-3 backdrop-blur-sm">
        <Logo />

        <DossierSelector onDemanderCreation={ouvrirCreation} />

        <Button variant="primary" onClick={() => ouvrirCreation()}>
          ＋ Nouveau dossier
        </Button>

        <div className="ml-auto flex items-center gap-2">
          <span className="text-micro uppercase tracking-wide text-warmgray">Droit</span>
          <select
            className="input w-auto py-2 text-sm"
            value={juridictionActive}
            onChange={(e) => void definirJuridictionActive(e.target.value)}
            aria-label="Juridiction active"
          >
            {sources.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <FullscreenToggle />
          <Link
            to="/app/parametres"
            className="rounded-md p-1.5 text-warmgray transition-colors hover:bg-surface-2 hover:text-ivory"
            aria-label="Paramètres"
            title="Paramètres"
          >
            <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="10" cy="10" r="2.6" />
              <path d="M10 2.5v2M10 15.5v2M17.5 10h-2M4.5 10h-2M15.3 4.7l-1.4 1.4M6.1 13.9l-1.4 1.4M15.3 15.3l-1.4-1.4M6.1 6.1 4.7 4.7" />
            </svg>
          </Link>
        </div>
      </header>

      {modalOuvert && (
        <NouveauDossierModal nomInitial={nomPrerempli} onFermer={() => setModalOuvert(false)} />
      )}
    </>
  );
}
