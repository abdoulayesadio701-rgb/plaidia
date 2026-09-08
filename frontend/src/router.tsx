/**
 * router.tsx — Arborescence des routes de Plaid'IA.
 *
 * Toutes les routes d'action (Arsenal, Chemise, Grimoire, Carnet, Greffier)
 * sont générées depuis src/config/navigation.ts — la même source qui pilote
 * la Sidebar — et rendent pour l'instant <PagePlaceholder>. Remplacez
 * chaque `element` par la vraie page au fur et à mesure de son
 * implémentation ; le chemin (item.path) ne change pas.
 */

import type { ReactElement } from "react";
import { createBrowserRouter } from "react-router-dom";
import AppLayout from "@/layout/AppLayout";
import HomePage from "@/pages/HomePage";
import ParametresPage from "@/pages/ParametresPage";
import LandingPage from "@/pages/LandingPage";
import ConnexionPage from "@/pages/ConnexionPage";
import NotFoundPage from "@/pages/NotFoundPage";
import Styleguide from "@/pages/Styleguide";
import ChatPage from "@/pages/ChatPage";
import AnalyserConclusionsPage from "@/pages/arsenal/AnalyserConclusionsPage";
import ResumerDossierPage from "@/pages/arsenal/ResumerDossierPage";
import PlanPlaidoiriePage from "@/pages/arsenal/PlanPlaidoiriePage";
import SimulateurObjectionsPage from "@/pages/arsenal/SimulateurObjectionsPage";
import RapportCompletPage from "@/pages/arsenal/RapportCompletPage";
import AnalyseStylePage from "@/pages/arsenal/AnalyseStylePage";
import DossiersPage from "@/pages/chemise/DossiersPage";
import HistoriqueDossierPage from "@/pages/chemise/HistoriqueDossierPage";
import PreparerDossierPage from "@/pages/chemise/PreparerDossierPage";
import ConsulterJurisprudencePage from "@/pages/grimoire/ConsulterJurisprudencePage";
import CollecterJurisprudencePage from "@/pages/grimoire/CollecterJurisprudencePage";
import GererJurisprudencePage from "@/pages/grimoire/GererJurisprudencePage";
import GererCorpusPage from "@/pages/grimoire/GererCorpusPage";
import PrendreNotePage from "@/pages/carnet/PrendreNotePage";
import ConsulterNotesPage from "@/pages/carnet/ConsulterNotesPage";
import NoteClientPage from "@/pages/carnet/NoteClientPage";
import TraduirePage from "@/pages/carnet/TraduirePage";
import ChronologiePage from "@/pages/greffier/ChronologiePage";
import ExtractionPage from "@/pages/greffier/ExtractionPage";
import ClassementPage from "@/pages/greffier/ClassementPage";
import CoherencePage from "@/pages/greffier/CoherencePage";
import RechercheTransversalePage from "@/pages/greffier/RechercheTransversalePage";
import PvAudiencePage from "@/pages/greffier/PvAudiencePage";
import VerificationProceduralePage from "@/pages/greffier/VerificationProceduralePage";
import PagePlaceholder from "@/components/PagePlaceholder";
import { allNavItems } from "@/config/navigation";

// Pages réellement implémentées, indexées par chemin -- toute route de
// navigation.ts qui n'y figure pas retombe sur <PagePlaceholder>. Retirer
// une entrée d'ici n'est jamais nécessaire ; en ajouter une suffit à
// "activer" la vraie page pour ce chemin.
const PAGES_IMPLEMENTEES: Record<string, ReactElement> = {
  "/chat": <ChatPage />,
  "/arsenal/analyser": <AnalyserConclusionsPage />,
  "/arsenal/resumer": <ResumerDossierPage />,
  "/arsenal/plan": <PlanPlaidoiriePage />,
  "/arsenal/simulateur": <SimulateurObjectionsPage />,
  "/arsenal/rapport-complet": <RapportCompletPage />,
  "/arsenal/style": <AnalyseStylePage />,
  "/chemise/dossiers": <DossiersPage />,
  "/chemise/historique": <HistoriqueDossierPage />,
  "/chemise/preparer": <PreparerDossierPage />,
  "/grimoire/jurisprudence": <ConsulterJurisprudencePage />,
  "/grimoire/collecter": <CollecterJurisprudencePage />,
  "/grimoire/gerer": <GererJurisprudencePage />,
  "/grimoire/corpus": <GererCorpusPage />,
  "/carnet/note": <PrendreNotePage />,
  "/carnet/notes": <ConsulterNotesPage />,
  "/carnet/note-client": <NoteClientPage />,
  "/carnet/traduire": <TraduirePage />,
  "/greffier/chronologie": <ChronologiePage />,
  "/greffier/extraction": <ExtractionPage />,
  "/greffier/classement": <ClassementPage />,
  "/greffier/coherence": <CoherencePage />,
  "/greffier/recherche": <RechercheTransversalePage />,
  "/greffier/pv-audience": <PvAudiencePage />,
  // Même page pour les deux espaces : voir l'en-tête de
  // VerificationProceduralePage.tsx (le prompt système sert avocat ET greffier).
  "/greffier/verification-procedurale": <VerificationProceduralePage />,
  "/arsenal/verification-procedurale": <VerificationProceduralePage />,
};

const routesActions = allNavItems().map((item) => ({
  path: item.path.slice(1), // relatif au parent AppLayout ("arsenal/analyser", pas "/arsenal/analyser")
  element: PAGES_IMPLEMENTEES[item.path] ?? <PagePlaceholder title={item.label} />,
}));

export const router = createBrowserRouter([
  // "/" est la vitrine publique (partageable, sans chrome applicatif) --
  // l'app elle-même vit sous "/app" pour que ce chemin reste libre. Voir
  // LandingPage.tsx ; son bouton "Essayer la démo" mène à /app/chemise/dossiers.
  { path: "/", element: <LandingPage /> },
  // /styleguide a son propre habillage complet (hero, nav interne) -- rendu
  // hors AppLayout pour ne pas empiler deux barres de navigation.
  { path: "/styleguide", element: <Styleguide /> },
  // Écran d'accès, hors AppLayout -- voir l'en-tête de ConnexionPage.tsx :
  // formulaire non relié à une authentification réelle (aucun backend de
  // comptes n'existe aujourd'hui), à connecter plus tard si besoin.
  { path: "/connexion", element: <ConnexionPage /> },
  {
    path: "/app",
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      // Hors de navigation.ts : réglage transversal accessible en permanence
      // depuis la TopBar, pas propre à un espace de travail (avocat/greffier).
      { path: "parametres", element: <ParametresPage /> },
      ...routesActions,
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  // Filet de sécurité pour tout chemin hors /app non reconnu (ex. lien
  // cassé) -- NotFoundPage renvoie vers "/", toujours valide.
  { path: "*", element: <NotFoundPage /> },
]);
