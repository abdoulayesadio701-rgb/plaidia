/**
 * RechercheGlobaleModal — vraie palette de recherche globale (voir
 * AUDIT_TASKBAR.md, étape 3), accessible depuis TaskBar et le raccourci
 * clavier Ctrl/Cmd+K (voir hooks/useRaccourciRecherche.ts). N'ajoute AUCUN
 * nouveau backend : réutilise exactement le même endpoint et le même
 * composant de résultats que DossiersPage (dossiersApi.rechercherDossiers
 * → RechercheDossierResultats), simplement dans une fenêtre accessible de
 * partout plutôt que sur une seule page.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { dossiers as dossiersApi } from "@/api";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useAppStore } from "@/store/useAppStore";
import Modal from "./Modal";
import RechercheDossierResultats from "./RechercheDossierResultats";

interface RechercheGlobaleModalProps {
  onFermer: () => void;
}

export default function RechercheGlobaleModal({ onFermer }: RechercheGlobaleModalProps) {
  const [terme, setTerme] = useState("");
  const navigate = useNavigate();
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);

  const { data: resultats, loading, error, executer, reinitialiser } = useLazyAction((t: string) => dossiersApi.rechercherDossiers(t));

  useEffect(() => {
    if (!terme.trim()) {
      reinitialiser();
      return;
    }
    const t = window.setTimeout(() => void executer(terme.trim()), 300);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terme]);

  const ouvrir = (dossierId: number) => {
    selectionnerDossier(dossierId);
    navigate("/app/chemise/historique");
    onFermer();
  };

  return (
    <Modal titre="Recherche globale" onFermer={onFermer} largeurMax="max-w-2xl" kicker="Tous vos dossiers, faits, parties et analyses">
      <div className="space-y-4">
        <input
          autoFocus
          className="input"
          placeholder="Rechercher un dossier, un fait, une partie, une analyse…"
          value={terme}
          onChange={(e) => setTerme(e.target.value)}
        />

        {terme.trim() ? (
          <div className="max-h-[55vh] overflow-y-auto">
            <RechercheDossierResultats
              resultats={resultats}
              loading={loading}
              erreur={error}
              terme={terme.trim()}
              onRelancer={() => void executer(terme.trim())}
              onOuvrir={ouvrir}
            />
          </div>
        ) : (
          <p className="py-6 text-center text-sm text-muted">Commencez à taper pour rechercher dans tous vos dossiers.</p>
        )}
      </div>
    </Modal>
  );
}
