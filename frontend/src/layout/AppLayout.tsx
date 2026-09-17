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
import RechercheGlobaleModal from "@/components/RechercheGlobaleModal";

export default function AppLayout() {
  const chargerDossiers = useAppStore((s) => s.chargerDossiers);
  const chargerJuridictionActive = useAppStore((s) => s.chargerJuridictionActive);
  const chargerSourcesJuridictions = useAppStore((s) => s.chargerSourcesJuridictions);
  const chargerCompteursAttente = useAppStore((s) => s.chargerCompteursAttente);
  const chargerConfiguration = useAppStore((s) => s.chargerConfiguration);
  const chargerEpingles = useAppStore((s) => s.chargerEpingles);
  const rechercheGlobaleOuverte = useAppStore((s) => s.rechercheGlobaleOuverte);
  const ouvrirRechercheGlobale = useAppStore((s) => s.ouvrirRechercheGlobale);
  const fermerRechercheGlobale = useAppStore((s) => s.fermerRechercheGlobale);

  useSuivreRecents();

  // Raccourci clavier Ctrl/Cmd+K -- palette de recherche accessible de
  // partout dans l'app, pas seulement via le bouton de TaskBar (voir §11
  // de la demande : "recherche globale").
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        ouvrirRechercheGlobale();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [ouvrirRechercheGlobale]);

  useEffect(() => {
    void chargerDossiers();
    void chargerJuridictionActive();
    void chargerSourcesJuridictions();
    void chargerCompteursAttente();
    void chargerConfiguration();
    void chargerEpingles();
    // Sous 768px, la sidebar est un tiroir caché par défaut (voir
    // Sidebar.tsx, useAppStore.sidebarMobileOuverte) -- plus besoin de
    // repli en rail d'icônes au montage comme avant, le tiroir superposé
    // remplace entièrement ce pis-aller.
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
      {rechercheGlobaleOuverte && <RechercheGlobaleModal onFermer={fermerRechercheGlobale} />}
    </div>
  );
}
