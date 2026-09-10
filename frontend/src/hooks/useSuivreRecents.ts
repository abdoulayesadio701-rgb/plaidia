/**
 * useSuivreRecents — enregistre la page courante dans "Récents" (voir
 * config/recents.ts) à chaque changement de route ou de dossier actif.
 * Monté une seule fois dans AppLayout. Ignore les chemins hors de
 * navigation.ts (accueil, paramètres...) sauf ceux explicitement nommés
 * ci-dessous, pour ne jamais enregistrer une entrée sans libellé lisible.
 */

import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { findNavItem } from "@/config/navigation";
import { ajouterRecent } from "@/config/recents";
import { useAppStore, useDossierActif } from "@/store/useAppStore";

/** Routes applicatives hors de navigation.ts (voir router.tsx) -- libellé
 * lisible propre à chacune, pour ne pas les exclure de "Récents". */
const LIBELLES_HORS_NAVIGATION: Record<string, string> = {
  "/": "Accueil",
  "/parametres": "Paramètres",
};

export function useSuivreRecents() {
  const location = useLocation();
  const dossierActif = useDossierActif();
  const dossierActifId = useAppStore((s) => s.dossierActifId);

  useEffect(() => {
    const chemin = location.pathname.replace(/^\/app/, "") || "/";
    const item = findNavItem(chemin);
    const label = item?.label ?? LIBELLES_HORS_NAVIGATION[chemin];
    if (!label) return; // route sans libellé connu (404, page non implémentée...) -- pas d'entrée fantôme

    ajouterRecent({
      id: `${chemin}::${dossierActifId ?? "sans-dossier"}`,
      path: chemin,
      label,
      dossierId: dossierActifId,
      dossierNom: dossierActif?.nom ?? null,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname, dossierActifId]);
}
