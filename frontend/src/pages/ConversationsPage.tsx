/**
 * ConversationsPage — /conversations. Historique global de toutes les
 * conversations de chat (rattachées à un dossier ou non), avec recherche par
 * titre et filtre par dossier. Complète HistoriqueDossierPage.tsx (qui
 * n'affiche que les conversations du dossier actif) sans le dupliquer --
 * même convention de réouverture (/app/chat?conversation_id=...), même
 * source de données (GET /api/chat/conversations, déjà utilisé nulle part
 * côté UI jusqu'ici).
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { chat as chatApi } from "@/api";
import type { ConversationResume } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

function formaterDate(iso: string, langue: string): string {
  try {
    const locale = langue === "en" ? "en-GB" : "fr-FR";
    return new Date(iso).toLocaleDateString(locale, { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

interface CarteConversationProps {
  conversation: ConversationResume;
  nomDossier: string | null;
  langue: string;
  onSupprimee: (id: number) => void;
}

function CarteConversation({ conversation, nomDossier, langue, onSupprimee }: CarteConversationProps) {
  const { t } = useTranslation();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [confirmation, setConfirmation] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);

  const supprimer = async () => {
    setSuppressionEnCours(true);
    try {
      await chatApi.supprimerConversation(conversation.id);
      onSupprimee(conversation.id);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("conversationsPage.echecSuppression"));
      setSuppressionEnCours(false);
      setConfirmation(false);
    }
  };

  return (
    <div className="card flex items-center justify-between gap-4 p-4">
      <Link to={`/app/chat?conversation_id=${conversation.id}`} className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-ivory">{conversation.titre}</p>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
          <span>{formaterDate(conversation.date_modification, langue)}</span>
          <span className="badge border-gold-600/30 bg-surface-2 text-warmgray">
            {nomDossier ?? t("conversationsPage.sansDossier")}
          </span>
        </div>
      </Link>
      <div className="flex shrink-0 items-center gap-2 text-xs">
        {!confirmation ? (
          <button onClick={() => setConfirmation(true)} className="text-muted hover:text-risk-high">
            {t("conversationsPage.supprimer")}
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-warmgray">{t("conversationsPage.confirmer")}</span>
            <button disabled={suppressionEnCours} onClick={() => void supprimer()} className="font-semibold text-risk-high hover:underline">
              {t("conversationsPage.oui")}
            </button>
            <button onClick={() => setConfirmation(false)} className="text-warmgray hover:underline">
              {t("commun.annuler")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ConversationsPage() {
  const { t, i18n } = useTranslation();
  const dossiers = useAppStore((s) => s.dossiers);
  const dossiersCharges = useAppStore((s) => s.dossiersCharges);
  const chargerDossiers = useAppStore((s) => s.chargerDossiers);

  const [recherche, setRecherche] = useState("");
  const [dossierFiltre, setDossierFiltre] = useState("");

  useEffect(() => {
    if (!dossiersCharges) void chargerDossiers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { data: conversations, loading, error, reload } = useAsync(() => chatApi.listerConversations(), []);

  const nomsDossiers = useMemo(() => new Map(dossiers.map((d) => [d.id, d.nom])), [dossiers]);

  const conversationsFiltrees = useMemo(() => {
    if (!conversations) return null;
    const terme = recherche.trim().toLowerCase();
    return conversations.filter((c) => {
      if (terme && !c.titre.toLowerCase().includes(terme)) return false;
      if (dossierFiltre === "sans" && c.dossier_id !== null) return false;
      if (dossierFiltre && dossierFiltre !== "sans" && c.dossier_id !== Number(dossierFiltre)) return false;
      return true;
    });
  }, [conversations, recherche, dossierFiltre]);

  const filtreActif = recherche.trim() !== "" || dossierFiltre !== "";

  return (
    <div className="space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.poserQuestion")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("conversationsPage.titre")}</h1>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <input
          className="input max-w-xs"
          placeholder={t("conversationsPage.rechercherPlaceholder")}
          aria-label={t("conversationsPage.rechercherAria")}
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
        />
        <select
          className="input w-auto"
          aria-label={t("conversationsPage.filtrerParDossier")}
          value={dossierFiltre}
          onChange={(e) => setDossierFiltre(e.target.value)}
        >
          <option value="">{t("conversationsPage.tousLesDossiers")}</option>
          <option value="sans">{t("conversationsPage.sansDossier")}</option>
          {dossiers.map((d) => (
            <option key={d.id} value={d.id}>
              {d.nom}
            </option>
          ))}
        </select>
      </div>

      {loading && <SkeletonList count={4} />}

      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && conversationsFiltrees && conversationsFiltrees.length === 0 && !filtreActif && (
        <EmptyState titre={t("conversationsPage.aucuneConversationTitre")} description={t("conversationsPage.aucuneConversationDescription")} />
      )}

      {!loading && !error && conversationsFiltrees && conversationsFiltrees.length === 0 && filtreActif && (
        <EmptyState titre={t("conversationsPage.aucunResultatTitre")} description={t("conversationsPage.aucunResultatDescription")} />
      )}

      {!loading && !error && conversationsFiltrees && conversationsFiltrees.length > 0 && (
        <div className="space-y-2">
          {conversationsFiltrees.map((conversation) => (
            <CarteConversation
              key={conversation.id}
              conversation={conversation}
              nomDossier={conversation.dossier_id !== null ? nomsDossiers.get(conversation.dossier_id) ?? null : null}
              langue={i18n.language}
              onSupprimee={reload}
            />
          ))}
        </div>
      )}
    </div>
  );
}
