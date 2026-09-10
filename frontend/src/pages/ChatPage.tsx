/**
 * ChatPage — "Poser une question", reprend PlaidIAApp._envoyer_message_chat
 * (gui.py) en streaming SSE web. Voir les composants réutilisés :
 * RichOutput (rendu markdown léger + surlignage "À VÉRIFIER"),
 * TexteLongModal (coller un réquisitoire/des conclusions), Button, Modal.
 */

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { chat as chatApi, dossiers as dossiersApi } from "@/api";
import type { MessageChat, Verification } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Logo from "@/components/Logo";
import Button from "@/components/Button";
import FileDropZone from "@/components/FileDropZone";
import RichOutput from "@/components/RichOutput";
import TexteLongModal from "@/components/TexteLongModal";
import VerificationPanel from "@/components/VerificationPanel";
import PinButton from "@/components/PinButton";

interface StatutRecherche {
  enCours: boolean;
  resultat: { n_articles: number; n_jurisprudence: number } | null;
}

interface PieceJointe {
  id: string;
  nom: string;
  texte: string;
  caracteres: number;
}

/** Compose le contenu réellement envoyé au modèle : le message tapé, suivi
 * de chaque document joint sous un en-tête clair -- même convention que
 * construire_contexte_dossier/controler_coherence côté backend ("---
 * Document : X ---"). Le contenu du document reste une DONNÉE à analyser,
 * jamais une instruction (voir EDITION_SYSTEM_PROMPT pour le précédent) --
 * ce n'est jamais le fichier brut qui part au modèle, seulement le texte
 * déjà extrait côté serveur (extract.py). */
function composerContenuAvecPiecesJointes(messageTape: string, pieces: PieceJointe[]): string {
  const message = messageTape.trim() || (pieces.length > 0 ? "Analyse le ou les documents joints." : "");
  if (pieces.length === 0) return message;
  const blocs = pieces.map((p) => `--- Document joint : ${p.nom} ---\n${p.texte}`).join("\n\n");
  return `${message}\n\n${blocs}`;
}

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const chatHistorique = useAppStore((s) => s.chatHistorique);
  const ajouterMessageChat = useAppStore((s) => s.ajouterMessageChat);
  const remplacerDernierMessageChat = useAppStore((s) => s.remplacerDernierMessageChat);
  const retirerDernierMessageSiVide = useAppStore((s) => s.retirerDernierMessageSiVide);
  const reinitialiserChat = useAppStore((s) => s.reinitialiserChat);
  const chargerConversationChat = useAppStore((s) => s.chargerConversationChat);
  const dossierActifId = useAppStore((s) => s.dossierActifId);
  const juridictionActive = useAppStore((s) => s.juridictionActive);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const [texte, setTexte] = useState("");
  const [rechercheLive, setRechercheLive] = useState(false);
  const [genererEnCours, setGenererEnCours] = useState(false);
  const [statutRecherche, setStatutRecherche] = useState<StatutRecherche | null>(null);
  // Additif (§10) : la vérification multi-agents ne porte que sur le
  // dernier message assistant reçu -- réinitialisée à chaque nouvel envoi,
  // jamais persistée dans l'historique (voir ChatStreamCallbacks.onVerification).
  const [verificationDerniereReponse, setVerificationDerniereReponse] = useState<Verification | null>(null);
  const [modalTexteLongOuverte, setModalTexteLongOuverte] = useState(false);
  const [indexMessageCopie, setIndexMessageCopie] = useState<number | null>(null);
  const [piecesJointes, setPiecesJointes] = useState<PieceJointe[]>([]);
  const [importPieceJointeEnCours, setImportPieceJointeEnCours] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const conteneurRef = useRef<HTMLDivElement>(null);

  const conversationIdParam = searchParams.get("conversation_id");
  const dossierIdParam = searchParams.get("dossier_id");
  const dossierIdDepuisUrl = dossierIdParam && /^\d+$/.test(dossierIdParam) ? Number(dossierIdParam) : null;
  const dossierIdChat = dossierIdDepuisUrl ?? dossierActifId;
  const chatConversationId = useAppStore((s) => s.chatConversationId);

  useEffect(() => {
    if (!conversationIdParam) return;
    const conversationId = Number(conversationIdParam);
    if (!Number.isInteger(conversationId) || conversationId <= 0) {
      pousserToast("error", "Le lien de conversation est invalide.");
      return;
    }
    let actif = true;
    void chatApi
      .obtenirConversation(conversationId)
      .then((conversation) => {
        if (actif) chargerConversationChat(conversation.id, conversation.historique);
      })
      .catch((e) => {
        if (actif) pousserToast("error", e instanceof Error ? e.message : "Impossible de charger cette conversation.");
      });
    return () => {
      actif = false;
    };
  }, [conversationIdParam, chargerConversationChat, pousserToast]);

  // Défilement automatique vers le dernier message -- pas de scrollIntoView
  // animé ici : à chaque fragment reçu pendant le streaming, un défilement
  // "smooth" répété deviendrait saccadé. scrollTop direct = instantané.
  useEffect(() => {
    const el = conteneurRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chatHistorique]);

  // Zone de saisie qui grandit avec son contenu, plafonnée pour ne pas
  // avaler toute la page si on colle un pavé de texte.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [texte]);

  const sauvegarderConversation = async () => {
    const { chatHistorique: historique, chatConversationId } = useAppStore.getState();
    if (historique.length === 0) return;
    try {
      if (chatConversationId === null) {
        const premierMessage = historique.find((m) => m.role === "user")?.content.trim() ?? "";
        let titre = premierMessage.replace(/\s+/g, " ").slice(0, 60);
        if (premierMessage.length > 60) titre += "…";
        const conversation = await chatApi.creerConversation(titre || "Conversation sans titre", historique, dossierIdChat);
        // `historique` est un tableau immuable (chaque action du store en
        // recrée un) : s'il a changé pendant l'appel réseau (ex. "Nouvelle
        // conversation" cliqué juste après un arrêt de génération), ne pas
        // réattribuer après coup un id à un historique qui n'est plus le bon.
        if (useAppStore.getState().chatHistorique === historique) {
          chargerConversationChat(conversation.id, historique);
        }
      } else {
        await chatApi.mettreAJourConversation(chatConversationId, historique);
      }
    } catch {
      // Sauvegarde silencieuse, à l'identique de gui.py -- un échec ici ne
      // doit jamais interrompre la conversation en cours.
    }
  };

  const envoyerMessage = async (contenuBrut: string) => {
    if (genererEnCours) return;
    const contenu = composerContenuAvecPiecesJointes(contenuBrut, piecesJointes);
    if (!contenu) return;

    const historiqueEnvoi: MessageChat[] = [...useAppStore.getState().chatHistorique, { role: "user", content: contenu }];

    ajouterMessageChat({ role: "user", content: contenu });
    ajouterMessageChat({ role: "assistant", content: "" }); // rempli au fil du flux SSE
    setTexte("");
    setPiecesJointes([]);
    setStatutRecherche(rechercheLive ? { enCours: true, resultat: null } : null);
    setVerificationDerniereReponse(null);
    setGenererEnCours(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;
    let accumulateur = "";

    await chatApi.streamChat(
      historiqueEnvoi,
      { rechercheLive, juridiction: juridictionActive, dossierId: dossierIdChat, signal: controller.signal },
      {
        onRechercheDebut: () => {
          // eslint-disable-next-line no-console
          console.log("[chat] recherche_debut");
          setStatutRecherche({ enCours: true, resultat: null });
        },
        onRechercheResultat: (data) => {
          // eslint-disable-next-line no-console
          console.log("[chat] recherche_resultat", data);
          setStatutRecherche({ enCours: false, resultat: data });
        },
        onDelta: (fragment) => {
          // eslint-disable-next-line no-console
          console.log("[chat] delta", JSON.stringify(fragment));
          accumulateur += fragment;
          remplacerDernierMessageChat(accumulateur);
        },
        onVerification: (verification) => {
          // eslint-disable-next-line no-console
          console.log("[chat] verification", verification.statut_global);
          setVerificationDerniereReponse(verification);
        },
        onDone: () => {
          // eslint-disable-next-line no-console
          console.log("[chat] done -- longueur finale:", accumulateur.length);
          setGenererEnCours(false);
          abortControllerRef.current = null;
          void sauvegarderConversation();
        },
        onError: (message) => {
          // eslint-disable-next-line no-console
          console.log("[chat] error", message);
          setGenererEnCours(false);
          abortControllerRef.current = null;
          // Sans ça, une erreur survenue avant le moindre fragment (ex. clé
          // API invalide) laisse une bulle assistant vide affichée sans
          // aucune explication visible -- ça se lit comme un blocage, même
          // si ce toast s'est bien déclenché à côté.
          retirerDernierMessageSiVide();
          pousserToast("error", message);
        },
      }
    );
  };

  const annulerGeneration = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setGenererEnCours(false);
    // Une génération arrêtée volontairement peut déjà contenir une réponse
    // partielle utile -- autant la conserver dans l'historique persistant,
    // plutôt que de la perdre silencieusement.
    void sauvegarderConversation();
  };

  const nouvelleConversation = () => {
    if (genererEnCours) annulerGeneration();
    reinitialiserChat();
    setStatutRecherche(null);
    setVerificationDerniereReponse(null);
    setPiecesJointes([]);
  };

  // Extraction du texte du fichier joint, sans l'envoyer -- l'utilisateur
  // voit le document apparaître comme une pièce jointe avant de composer
  // et d'envoyer son message (voir ARCHITECTURE_MULTI_AGENTS.md §8 de la
  // demande initiale). Si un dossier est actif, réutilise importerDocument
  // (le texte est aussi ajouté aux faits du dossier, comme partout ailleurs
  // dans l'app) ; sinon extraireFichier, qui n'écrit rien en base.
  const joindreFichier = async (fichier: File) => {
    setImportPieceJointeEnCours(true);
    try {
      const resultat = dossierActifId
        ? await dossiersApi.importerDocument(dossierActifId, fichier)
        : await dossiersApi.extraireFichier(fichier);
      setPiecesJointes((liste) => [
        ...liste,
        { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, nom: resultat.nom_fichier, texte: resultat.texte_extrait, caracteres: resultat.caracteres_extraits },
      ]);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'import du fichier.");
    } finally {
      setImportPieceJointeEnCours(false);
    }
  };

  const retirerPieceJointe = (id: string) => setPiecesJointes((liste) => liste.filter((p) => p.id !== id));

  const onKeyDownComposer = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void envoyerMessage(texte);
    }
  };

  const copierMessage = async (index: number, contenu: string) => {
    try {
      await navigator.clipboard.writeText(contenu);
      setIndexMessageCopie(index);
      setTimeout(() => setIndexMessageCopie((i) => (i === index ? null : i)), 1500);
    } catch {
      pousserToast("error", "Impossible de copier – presse-papiers indisponible dans ce contexte.");
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* En-tête de la vue chat */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-gold-600/15 pb-4">
        {chatConversationId !== null && <PinButton type="conversation" referenceId={chatConversationId} dossierId={dossierIdChat} libelle="Conversation de chat" />}
        <label className="flex cursor-pointer items-center gap-2.5 text-sm text-warmgray">
          <button
            type="button"
            role="switch"
            aria-checked={rechercheLive}
            onClick={() => setRechercheLive((v) => !v)}
            className={`relative h-5 w-9 shrink-0 rounded-pill transition-colors ${rechercheLive ? "bg-amethyst-400" : "bg-surface-3"}`}
          >
            <span
              className={`absolute top-0.5 h-4 w-4 rounded-pill bg-ivory transition-transform ${
                rechercheLive ? "translate-x-[18px]" : "translate-x-0.5"
              }`}
            />
          </button>
          Recherche live Légifrance / Judilibre
        </label>
        <Button variant="ghost" onClick={nouvelleConversation}>
          🔄 Nouvelle conversation
        </Button>
      </div>

      {/* Fil de discussion */}
      <div ref={conteneurRef} className="flex-1 space-y-4 overflow-y-auto pb-2 pr-1">
        {chatHistorique.length === 0 && (
          <p className="py-10 text-center text-sm text-warmgray">
            Formulez votre question ci-dessous. La conversation demeure active tant que vous ne cliquez pas sur
            « Nouvelle conversation ».
          </p>
        )}

        {chatHistorique.map((message, index) => {
          const estUtilisateur = message.role === "user";
          const estDernier = index === chatHistorique.length - 1;

          return (
            <div key={index} className={`flex items-start gap-3 ${estUtilisateur ? "justify-end" : "justify-start"}`}>
              {!estUtilisateur && (
                <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-gold-600/40 bg-surface-2">
                  <Logo showWordmark={false} iconClassName="h-4 w-4 text-gold-500" />
                </div>
              )}

              <div
                className={`group relative max-w-[75%] rounded-md px-4 py-3 ${
                  estUtilisateur ? "border border-amethyst-400/40 bg-surface-2 text-ivory" : "card"
                }`}
              >
                {!estUtilisateur && estDernier && statutRecherche && (
                  <p className="mb-2 text-xs text-warmgray">
                    {statutRecherche.enCours
                      ? "🔍 Recherche en direct sur Légifrance et Judilibre…"
                      : statutRecherche.resultat &&
                        `→ ${statutRecherche.resultat.n_articles} article(s) de loi, ${statutRecherche.resultat.n_jurisprudence} décision(s) trouvés.`}
                  </p>
                )}

                {estUtilisateur ? (
                  <p className="whitespace-pre-wrap text-body">{message.content}</p>
                ) : message.content ? (
                  <RichOutput texte={message.content} prose={false} />
                ) : (
                  estDernier &&
                  genererEnCours && (
                    <span className="inline-flex gap-1 py-1" aria-label="L'agent réfléchit">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold-500 [animation-delay:-0.3s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold-500 [animation-delay:-0.15s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold-500" />
                    </span>
                  )
                )}

                {!estUtilisateur && message.content && (
                  <button
                    onClick={() => copierMessage(index, message.content)}
                    className="absolute right-2 top-2 rounded-md p-1 text-warmgray opacity-0 transition-opacity hover:text-ivory group-hover:opacity-100"
                    aria-label="Copier la réponse"
                    title="Copier"
                  >
                    {indexMessageCopie === index ? "✓" : "⧉"}
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {!genererEnCours && verificationDerniereReponse && (
          <VerificationPanel verification={verificationDerniereReponse} />
        )}
      </div>

      {/* Zone de saisie */}
      <div className="mt-4 rounded-md border border-gold-600/20 bg-surface p-3">
        {genererEnCours && (
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="inline-flex items-center gap-1.5 text-warmgray">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amethyst-400" aria-hidden="true" />
              Génération en cours…
            </span>
            <button onClick={annulerGeneration} className="font-medium text-risk-high hover:underline">
              Arrêter
            </button>
          </div>
        )}

        {piecesJointes.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {piecesJointes.map((p) => (
              <span
                key={p.id}
                className="inline-flex items-center gap-1.5 rounded-pill border border-amethyst-400/40 bg-amethyst-400/10 px-2.5 py-1 text-xs text-amethyst-400"
              >
                📄 {p.nom} <span className="text-muted">({p.caracteres.toLocaleString("fr-FR")} car.)</span>
                <button
                  onClick={() => retirerPieceJointe(p.id)}
                  className="ml-0.5 text-amethyst-400/70 hover:text-amethyst-400"
                  aria-label={`Retirer ${p.nom}`}
                  disabled={genererEnCours}
                >
                  ✕
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2">
          <button
            type="button"
            onClick={() => setModalTexteLongOuverte(true)}
            className="btn-secondary shrink-0 text-xs"
            title="Coller un texte long (réquisitoire, conclusions...)"
          >
            📋 Texte long
          </button>
          <FileDropZone
            variante="compact"
            extensions={EXTENSIONS_DOCUMENT}
            multiple
            loading={importPieceJointeEnCours}
            disabled={genererEnCours}
            libelleBouton="📎 Joindre un fichier"
            className="shrink-0 text-xs"
            onFichiers={(fichiers) => {
              for (const fichier of Array.from(fichiers)) void joindreFichier(fichier);
            }}
          />
          <textarea
            ref={textareaRef}
            value={texte}
            onChange={(e) => setTexte(e.target.value)}
            onKeyDown={onKeyDownComposer}
            placeholder="Posez votre question, ou joignez un document… (Entrée pour envoyer, Maj+Entrée pour un saut de ligne)"
            rows={1}
            className="input flex-1 resize-none"
            disabled={genererEnCours}
          />
          <Button
            variant="primary"
            onClick={() => void envoyerMessage(texte)}
            disabled={genererEnCours || (!texte.trim() && piecesJointes.length === 0)}
            className="shrink-0"
          >
            Envoyer →
          </Button>
        </div>
      </div>

      {modalTexteLongOuverte && (
        <TexteLongModal
          titre="Coller un texte long"
          consigne="Collez ici le texte à analyser (réquisitoire, conclusions, jugement...) – il sera inséré dans la zone de saisie, à vous de compléter et d'envoyer."
          onFermer={() => setModalTexteLongOuverte(false)}
          onValider={(texteColle) => {
            setTexte((precedent) => (precedent ? `${precedent}\n\n${texteColle}` : texteColle));
            textareaRef.current?.focus();
          }}
        />
      )}
    </div>
  );
}
