/**
 * AppLayout — squelette général de l'app (voir PlaidIAApp._construire_interface
 * dans gui.py) : bandeau du haut, barre de commande, sidebar + zone
 * principale, barre de statut. Monté une fois par le routeur (route racine
 * imbriquée), <Outlet /> reçoit la page active.
 */

import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useAppStore } from "@/store/useAppStore";
import { useSuivreRecents } from "@/hooks/useSuivreRecents";
import TopBar from "./TopBar";
import TaskBar from "./TaskBar";
import CommandBar from "./CommandBar";
import Sidebar from "./Sidebar";
import StatusBar from "./StatusBar";
import DemoBanner from "./DemoBanner";
import ToastContainer from "@/components/ToastContainer";

export default function AppLayout() {
  const chargerDossiers = useAppStore((s) => s.chargerDossiers);
  const chargerJuridictionActive = useAppStore((s) => s.chargerJuridictionActive);
  const chargerSourcesJuridictions = useAppStore((s) => s.chargerSourcesJuridictions);
  const chargerCompteursAttente = useAppStore((s) => s.chargerCompteursAttente);
  const chargerConfiguration = useAppStore((s) => s.chargerConfiguration);
  const chargerEpingles = useAppStore((s) => s.chargerEpingles);
  const definirSidebarRepliee = useAppStore((s) => s.definirSidebarRepliee);

  useSuivreRecents();

  useEffect(() => {
    void chargerDossiers();
    void chargerJuridictionActive();
    void chargerSourcesJuridictions();
    void chargerCompteursAttente();
    void chargerConfiguration();
    void chargerEpingles();
    // Repli par défaut sur petit écran (< 768px) : une barre latérale de
    // 288px fixe ne laisserait presque rien au contenu sur un téléphone --
    // un simple réglage initial, pas un comportement forcé (l'avocat peut
    // toujours la redéplier via le bouton « » »).
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      definirSidebarRepliee(true);
    }
    // Chargement initial uniquement -- ces actions restent disponibles
    // individuellement pour un rafraîchissement manuel depuis les pages.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-void text-ivory">
      <DemoBanner />
      <TopBar />
      <TaskBar />
      <CommandBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      <StatusBar />
      <ToastContainer />
    </div>
  );
}
