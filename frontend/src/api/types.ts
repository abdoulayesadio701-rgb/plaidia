/**
 * types.ts — Types TypeScript alignés sur les schémas Pydantic du backend
 * (backend/app/schemas/*.py). Un fichier miroir par router pour retrouver
 * facilement la correspondance ; voir backend/README.md pour la liste des
 * routes et /docs pour le détail exact généré depuis le code.
 */

// ---------------------------------------------------------------------
// Dossiers (backend/app/schemas/dossiers.py)
// ---------------------------------------------------------------------

export interface Dossier {
  id: number;
  nom: string;
  numero_dossier?: string;
  domaine?: string;
  parties?: string;
  faits?: string;
  statut: string;
  date_creation: string;
}

export interface DossierCreateInput {
  nom: string;
  numero_dossier?: string;
  domaine?: string;
  parties?: string;
  faits?: string;
}

export interface DocumentImporte {
  nom_fichier: string;
  texte_extrait: string;
  caracteres_extraits: number;
}

export interface RechercheDossierResultat {
  dossier: Dossier;
  extraits: [string, string][];
}

export interface AnalyseHistorique {
  id: number;
  date: string;
  arguments: Argument[];
  points_attention: string[];
  statut: StatutDocument;
}

// ---------------------------------------------------------------------
// Analyse (backend/app/schemas/analyse.py)
// ---------------------------------------------------------------------

export type NiveauRisque = "Faible" | "Moyen" | "Élevé" | string;

export interface Raisonnement {
  probleme_de_droit: string;
  regle_applicable: string;
  application_aux_faits: string;
}

export interface Refutation {
  angle: string;
  piste: string;
}

export interface Argument {
  resume: string;
  fondement: string;
  raisonnement?: Raisonnement | null;
  risque: NiveauRisque;
  justification_risque: string;
  refutations: Refutation[];
}

// --- Vérification multi-agents (backend/app/schemas/verification.py) ------
// Bloc additif produit par le pipeline de vérification (voir
// ARCHITECTURE_MULTI_AGENTS.md) -- toujours optionnel, absent en mode démo
// ou si le garde-fou/pipeline n'est pas applicable à la fonctionnalité.

export type StatutVerification = "VERIFIE" | "PARTIELLEMENT_VERIFIE" | "A_VERIFIER" | "NON_VERIFIE" | string;
export type StatutConfiance = "VERIFIE" | "A_VERIFIER" | "INCERTAIN" | string;

export interface ElementVerifie {
  affirmation: string;
  statut: StatutVerification;
  commentaire: string;
}

export interface Critique {
  cible: string;
  type: string;
  commentaire: string;
  gravite: string;
}

export interface Verification {
  statut_global: StatutConfiance;
  elements: ElementVerifie[];
  critiques: Critique[];
  points_a_verifier: string[];
  synthese_utilisateur: string;
}

export interface ConclusionsResultat {
  arguments: Argument[];
  points_attention: string[];
  analyse_id?: number | null;
  verification?: Verification | null;
  statut: StatutDocument;
}

export type StatutDocument = "Brouillon" | "En cours" | "En révision" | "Validé" | "Final";

export interface ResumeResultat {
  resume_court: string;
  points_cles: string[];
  elements_manquants: string[];
}

export interface PointPlan {
  point: string;
  duree_minutes?: number | null;
  argument_cle: string;
  notes: string;
}

export interface PlanResultat {
  accroche: string;
  plan: PointPlan[];
  conclusion: string;
  points_attention: string[];
  verification?: Verification | null;
}

export interface Objection {
  origine: string;
  question: string;
  piege: string;
  piste_reponse: string;
}

export interface SimulateurResultat {
  objections: Objection[];
  point_le_plus_faible: string;
  verification?: Verification | null;
}

export interface RapportCompletResultat {
  analyse?: ConclusionsResultat | null;
  plan?: PlanResultat | null;
  simulateur: SimulateurResultat;
}

export interface ElementStyle {
  citation: string;
  commentaire: string;
}

export interface StyleResultat {
  langage_de_couverture: ElementStyle[];
  affirmations_absolues: ElementStyle[];
  voix_passive_suspecte: ElementStyle[];
  ruptures_registre: ElementStyle[];
  synthese_strategique: string;
}

export interface TraductionResultat {
  langue_detectee: string;
  langue_cible: string;
  texte_traduit: string;
}

// ---------------------------------------------------------------------
// Jurisprudence (backend/app/schemas/jurisprudence.py)
// ---------------------------------------------------------------------

export interface Notions {
  domaine: string;
  qualification_juridique: string;
  mots_cles_recherche: string[];
  but: string;
}

export interface ConsulterResultat {
  notions: Notions;
  reponse: string;
  verification?: Verification | null;
}

export interface DecisionCollectee {
  reference: string;
  resume: string;
  domaine?: string;
  source?: string;
}

export interface CollecterResultat {
  decisions: DecisionCollectee[];
  nombre_collecte: number;
}

export interface Jurisprudence {
  id: number;
  reference: string;
  resume?: string;
  domaine?: string;
  source?: string;
  validee: number;
}

export interface CorpusImportInput {
  source: string;
  contenu: string;
  pays?: string;
  type_texte?: string;
  domaine?: string;
  reference?: string;
  date_texte?: string;
}

export interface CorpusTexte {
  id: number;
  source: string;
  pays?: string;
  type_texte?: string;
  domaine?: string;
  reference?: string;
  date_texte?: string;
  statut?: string;
  contenu: string;
  validee: number;
  date_import: string;
}

// ---------------------------------------------------------------------
// Notes (backend/app/schemas/notes.py)
// ---------------------------------------------------------------------

export interface Note {
  id: number;
  note_brute: string;
  note_structuree?: string;
  actions: string[];
  points: string[];
  date_creation: string;
}

// ---------------------------------------------------------------------
// Greffier (backend/app/schemas/greffier.py)
// ---------------------------------------------------------------------

export interface Evenement {
  date: string;
  evenement: string;
}

export interface ChronologieResultat {
  periode_couverte: string;
  evenements: Evenement[];
  elements_manquants: string[];
}

export interface ExtractionResultat {
  dates: string[];
  personnes_et_parties: string[];
  references: string[];
  demandes: string[];
  decisions: string[];
}

export interface ClassementResultat {
  nature: string;
  justification: string;
  confiance: string;
}

export interface DocumentACoherence {
  nom_document: string;
  texte: string;
}

export interface Contradiction {
  sujet: string;
  document_1: string;
  document_2: string;
  gravite: string;
}

export interface CoherenceResultat {
  elements_par_document: Record<string, ExtractionResultat>;
  contradictions: Contradiction[];
  elements_coherents: string[];
  limites_analyse: string;
}

export interface Echeance {
  echeance: string;
  date: string;
  statut: string;
}

export interface VerificationProceduraleResultat {
  echeances_identifiees: Echeance[];
  actes_potentiellement_manquants: string[];
  points_attention: string[];
}

export interface PvAudienceResultat {
  texte: string;
}

export interface RequisitoireResultat {
  qualification_retenue: string;
  faits_et_elements_invoques: string[];
  circonstances_aggravantes: string[];
  circonstances_attenuantes: string[];
  peine_requise: string;
  points_attention: string[];
}

export interface RapportInstructionResultat {
  actes_instruction: string[];
  elements_a_charge: string[];
  elements_a_decharge: string[];
  mesures_ordonnees: string[];
  sens_propose: string;
  points_attention: string[];
}

// ---------------------------------------------------------------------
// Chat (backend/app/schemas/chat.py)
// ---------------------------------------------------------------------

export type RoleMessage = "user" | "assistant";

export interface MessageChat {
  role: RoleMessage;
  content: string;
}

export interface ConversationResume {
  id: number;
  titre: string;
  date_creation: string;
  date_modification: string;
  dossier_id: number | null;
}

export interface ConversationDetail extends ConversationResume {
  historique: MessageChat[];
}

// --- Chat contextuel (édition d'un résultat déjà affiché) -------------
// Voir ARCHITECTURE_CHAT_CONTEXTUEL.md — un seul mécanisme réutilisé par
// toutes les pages de génération, pas un chat par fonctionnalité.

export type FeatureChatContextuel =
  | "conclusions"
  | "plan"
  | "simulateur"
  | "note_client"
  | "chronologie"
  | "coherence"
  | "pv_audience"
  | "rapport_complet"
  | "resume"
  | "style"
  | "verification_procedurale"
  | "extraction"
  | "jurisprudence_consultation";

export interface ChatContextuelResultat {
  intent: string;
  scope: string;
  operation: string;
  parameters: Record<string, unknown>;
  resultat_modifie: unknown;
  reponse_agent: string;
}

/** Événements du flux SSE POST /api/chat/stream — voir backend/README.md.
 * "verification" (additif, ARCHITECTURE_MULTI_AGENTS.md §10) n'est envoyé
 * que si l'agent d'intention a jugé la question suffisamment substantielle
 * pour justifier le trio qualité -- absent la plupart du temps. */
export type ChatStreamEvent =
  | { event: "recherche_debut"; data: Record<string, never> }
  | { event: "recherche_resultat"; data: { n_articles: number; n_jurisprudence: number } }
  | { event: "delta"; data: { text: string } }
  | { event: "verification"; data: Verification }
  | { event: "done"; data: Record<string, never> }
  | { event: "error"; data: { detail: string } };

// ---------------------------------------------------------------------
// Versions (backend/app/schemas/versions.py)
// ---------------------------------------------------------------------

export interface VersionDocument {
  id: number;
  dossier_id?: number | null;
  feature: string;
  contenu: unknown;
  resume_modification?: string;
  auteur: "ia" | "utilisateur" | string;
  date_creation: string;
}

// ---------------------------------------------------------------------
// Épinglage (backend/app/schemas/epingles.py)
// ---------------------------------------------------------------------

export type TypeEpingle = "dossier" | "analyse";

export interface ElementEpingle {
  id: number;
  type: TypeEpingle;
  reference_id: number;
  dossier_id?: number | null;
  libelle: string;
  date_creation: string;
}

// ---------------------------------------------------------------------
// Intention (backend/app/schemas/intention.py)
// ---------------------------------------------------------------------

export interface Intention {
  action: string;
  confiance: "haute" | "moyenne" | "basse" | string;
  reformulation: string;
  duree_minutes?: number | null;
}
