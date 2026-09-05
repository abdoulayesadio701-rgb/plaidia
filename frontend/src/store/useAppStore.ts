/**
 * useAppStore — état global léger de Plaid'IA (Zustand, sans middleware
 * superflu) : dossier actif, espace actif, juridiction active, historique
 * du chat en cours, et les toasts d'erreur/info affichés par StatusBar.
 *
 * Reprend l'état que gui.py gardait sur `self` (PlaidIAApp.__init__) :
 * dossier_actuel, espace_actuel, source_juridique_active, historique_question.
 */

import { create } from "zustand";
import {
  config as configApi,
  dossiers as dossiersApi,
  jurisprudence as jurisprudenceApi,
  definirClePersonnelle as ecrireClePersonnelle,
  obtenirClePersonnelle,
} from "@/api";
import type { Dossier, MessageChat } from "@/api";
import type { Espace } from "@/config/navigation";

export type ToastType = "info" | "success" | "error";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface AppState {
  // --- Dossiers -----------------------------------------------------
  dossiers: Dossier[];
  dossierActifId: number | null;
  dossiersCharges: boolean;
  dossiersErreur: string | null;
  chargerDossiers: () => Promise<void>;
  selectionnerDossier: (id: number | null) => void;
  ajouterDossierLocal: (dossier: Dossier) => void;
  retirerDossierLocal: (id: number) => void;
  mettreAJourDossierLocal: (dossier: Dossier) => void;

  // --- Espace (Avocat / Greffier) -----------------------------------
  espaceActif: Espace;
  definirEspace: (espace: Espace) => void;

  // --- Juridiction active --------------------------------------------
  juridictionActive: string;
  /** Légifrance + sources du corpus multi-source déjà validées (Le Grimoire
   * les alimente, TopBar et Paramètres juridiques les consomment). */
  sourcesJuridictions: string[];
  chargerJuridictionActive: () => Promise<void>;
  definirJuridictionActive: (juridiction: string) => Promise<void>;
  chargerSourcesJuridictions: () => Promise<void>;

  // --- Le Grimoire : compteurs "en attente" (badge Sidebar) ----------
  jurisprudenceEnAttenteCount: number;
  corpusEnAttenteCount: number;
  chargerCompteursAttente: () => Promise<void>;

  // --- Chat (Poser une question) --------------------------------------
  chatHistorique: MessageChat[];
  chatConversationId: number | null;
  ajouterMessageChat: (message: MessageChat) => void;
  remplacerDernierMessageChat: (content: string) => void;
  reinitialiserChat: () => void;
  chargerConversationChat: (id: number, historique: MessageChat[]) => void;
  retirerDernierMessageSiVide: () => void;

  // --- Barre latérale --------------------------------------------------
  sidebarReplie: boolean;
  basculerSidebar: () => void;
  definirSidebarRepliee: (repliee: boolean) => void;

  // --- Configuration serveur (mode démo, voir GET /api/config) ---------
  demoMode: boolean;
  dossierDemoNom: string | null;
  configurationChargee: boolean;
  chargerConfiguration: () => Promise<void>;

  // --- Clé Anthropic personnelle ("Utiliser ma propre clé") ------------
  // Stockée uniquement dans sessionStorage (voir api/cleApiPersonnelle.ts) ;
  // ce champ du store n'est qu'un miroir pour que l'UI (bandeau démo,
  // pied de page) sache si une clé est active sans relire sessionStorage
  // à chaque rendu.
  clePersonnelleActive: boolean;
  definirClePersonnelle: (cle: string | null) => void;

  // --- Toasts ----------------------------------------------------------
  toasts: Toast[];
  pousserToast: (type: ToastType, message: string) => void;
  retirerToast: (id: string) => void;
}

const JURIDICTION_PAR_DEFAUT = "Légifrance (France)";

export const useAppStore = create<AppState>((set, get) => ({
  dossiers: [],
  dossierActifId: null,
  dossiersCharges: false,
  dossiersErreur: null,

  chargerDossiers: async () => {
    try {
      const liste = await dossiersApi.listerDossiers();
      set({ dossiers: liste, dossiersCharges: true, dossiersErreur: null });
    } catch (e) {
      const message = e instanceof Error ? e.message : "Impossible de charger les dossiers.";
      set({ dossiersErreur: message });
      get().pousserToast("error", message);
    }
  },

  selectionnerDossier: (id) => {
    set({ dossierActifId: id });
    // Changer de dossier n'a pas de sens à mélanger avec la conversation
    // en cours -- même règle que gui.py::_selectionner_dossier.
    get().reinitialiserChat();
  },

  ajouterDossierLocal: (dossier) => set((s) => ({ dossiers: [dossier, ...s.dossiers] })),

  retirerDossierLocal: (id) =>
    set((s) => ({
      dossiers: s.dossiers.filter((d) => d.id !== id),
      dossierActifId: s.dossierActifId === id ? null : s.dossierActifId,
    })),

  mettreAJourDossierLocal: (dossier) =>
    set((s) => ({ dossiers: s.dossiers.map((d) => (d.id === dossier.id ? dossier : d)) })),

  espaceActif: "avocat",
  definirEspace: (espace) => set({ espaceActif: espace }),

  juridictionActive: JURIDICTION_PAR_DEFAUT,
  sourcesJuridictions: [JURIDICTION_PAR_DEFAUT],

  chargerJuridictionActive: async () => {
    try {
      const { juridiction } = await jurisprudenceApi.obtenirJuridictionActive();
      set({ juridictionActive: juridiction });
    } catch {
      // Reste sur la valeur par défaut si le backend n'est pas joignable
      // au démarrage -- ne bloque jamais l'affichage de l'app.
    }
  },

  definirJuridictionActive: async (juridiction) => {
    set({ juridictionActive: juridiction }); // optimiste
    try {
      await jurisprudenceApi.definirJuridictionActive(juridiction);
    } catch (e) {
      get().pousserToast("error", e instanceof Error ? e.message : "Impossible d'enregistrer la juridiction.");
    }
  },

  chargerSourcesJuridictions: async () => {
    try {
      const sources = await jurisprudenceApi.sourcesCorpus();
      set({ sourcesJuridictions: sources });
    } catch {
      // Le sélecteur reste utilisable avec la seule juridiction par défaut
      // si le backend n'est pas joignable -- jamais bloquant.
    }
  },

  jurisprudenceEnAttenteCount: 0,
  corpusEnAttenteCount: 0,

  chargerCompteursAttente: async () => {
    try {
      const [jurisprudence, corpus] = await Promise.all([
        jurisprudenceApi.jurisprudenceEnAttente(),
        jurisprudenceApi.corpusEnAttente(),
      ]);
      set({ jurisprudenceEnAttenteCount: jurisprudence.length, corpusEnAttenteCount: corpus.length });
    } catch {
      // Le badge garde simplement sa dernière valeur connue.
    }
  },

  chatHistorique: [],
  chatConversationId: null,

  ajouterMessageChat: (message) => set((s) => ({ chatHistorique: [...s.chatHistorique, message] })),

  remplacerDernierMessageChat: (content) =>
    set((s) => {
      if (s.chatHistorique.length === 0) return s;
      const historique = [...s.chatHistorique];
      historique[historique.length - 1] = { ...historique[historique.length - 1], content };
      return { chatHistorique: historique };
    }),

  reinitialiserChat: () => set({ chatHistorique: [], chatConversationId: null }),

  // Si le flux échoue avant le moindre fragment (ex. clé API invalide), la
  // bulle assistant vide ajoutée en prévision du streaming (voir ChatPage::
  // envoyerMessage) ne doit pas rester affichée telle quelle : une bulle
  // vide sans aucune trace de ce qui s'est passé se lit comme "l'app est
  // bloquée", même si un toast d'erreur a bien été déclenché à côté (voir
  // ChatPage::onError). On ne retire QUE si elle est encore vide -- un
  // fragment partiel reçu avant l'erreur reste affiché, comme à l'arrêt
  // volontaire d'une génération.
  retirerDernierMessageSiVide: () =>
    set((s) => {
      const dernier = s.chatHistorique.at(-1);
      if (dernier && dernier.role === "assistant" && dernier.content === "") {
        return { chatHistorique: s.chatHistorique.slice(0, -1) };
      }
      return s;
    }),

  chargerConversationChat: (id, historique) => set({ chatConversationId: id, chatHistorique: historique }),

  sidebarReplie: false,
  basculerSidebar: () => set((s) => ({ sidebarReplie: !s.sidebarReplie })),
  definirSidebarRepliee: (repliee) => set({ sidebarReplie: repliee }),

  demoMode: false,
  dossierDemoNom: null,
  configurationChargee: false,

  chargerConfiguration: async () => {
    try {
      const config = await configApi.obtenirConfiguration();
      set({ demoMode: config.demo_mode, dossierDemoNom: config.dossier_demo_nom, configurationChargee: true });
    } catch {
      // Pas de bandeau démo si la config n'a pas pu être lue -- jamais
      // bloquant pour le reste de l'app.
      set({ configurationChargee: true });
    }
  },

  clePersonnelleActive: obtenirClePersonnelle() !== null,
  definirClePersonnelle: (cle) => {
    ecrireClePersonnelle(cle);
    set({ clePersonnelleActive: cle !== null && cle.trim() !== "" });
  },

  toasts: [],
  pousserToast: (type, message) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    set((s) => ({ toasts: [...s.toasts, { id, type, message }] }));
    if (typeof window !== "undefined") {
      window.setTimeout(() => get().retirerToast(id), 6000);
    }
  },
  retirerToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

/** Le dossier actif complet (ou null), dérivé de dossierActifId + dossiers. */
export function useDossierActif(): Dossier | null {
  return useAppStore((s) => s.dossiers.find((d) => d.id === s.dossierActifId) ?? null);
}
