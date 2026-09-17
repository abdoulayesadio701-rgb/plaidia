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

// Intervalle de rafraîchissement des générations en arrière-plan et des
// notifications de veille -- 5s pour les générations (un badge qui met
// une minute à refléter une génération terminée pendant qu'on regarde
// activement l'écran serait frustrant), 60s pour la veille (portée par
// une boucle serveur horaire de toute façon, voir backend/app/veille.py
// -- inutile de la solliciter aussi souvent que les générations).
const INTERVALLE_GENERATIONS_MS = 5000;
const INTERVALLE_VEILLE_MS = 60000;

export default function AppLayout() {
  const chargerDossiers = useAppStore((s) => s.chargerDossiers);
  const chargerJuridictionActive = useAppStore((s) => s.chargerJuridictionActive);
  const chargerSourcesJuridictions = useAppStore((s) => s.chargerSourcesJuridictions);
  const chargerCompteursAttente = useAppStore((s) => s.chargerCompteursAttente);
  const chargerConfiguration = useAppStore((s) => s.chargerConfiguration);
  const chargerEpingles = useAppStore((s) => s.chargerEpingles);
  const chargerGenerations = useAppStore((s) => s.chargerGenerations);
  const chargerNotificationsVeille = useAppStore((s) => s.chargerNotificationsVeille);
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
    void chargerGenerations();
    void chargerNotificationsVeille();
    // Sous 768px, la sidebar est un tiroir caché par défaut (voir
    // Sidebar.tsx, useAppStore.sidebarMobileOuverte) -- plus besoin de
    // repli en rail d'icônes au montage comme avant, le tiroir superposé
    // remplace entièrement ce pis-aller.
    // Chargement initial uniquement -- ces actions restent disponibles
    // individuellement pour un rafraîchissement manuel depuis les pages.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Rafraîchissement périodique -- une génération lancée depuis une page
  // doit continuer à être suivie (badge, historique) même après avoir
  // navigué ailleurs, exactement comme le thread d'arrière-plan de
  // gui.py::_lancer_generation survit à un changement d'écran. Monté une
  // seule fois ici (AppLayout, jamais démonté tant que l'app tourne),
  // pas dans chaque page qui pourrait déclencher une génération.
  useEffect(() => {
    const idGenerations = window.setInterval(() => void chargerGenerations(), INTERVALLE_GENERATIONS_MS);
    const idVeille = window.setInterval(() => void chargerNotificationsVeille(), INTERVALLE_VEILLE_MS);
    return () => {
      window.clearInterval(idGenerations);
      window.clearInterval(idVeille);
    };
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
