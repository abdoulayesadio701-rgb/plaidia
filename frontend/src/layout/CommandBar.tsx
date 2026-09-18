/**
 * CommandBar — barre de commande en langage naturel, sous le header.
 * Reprend _commande_naturelle() de gui.py : appelle /api/intention,
 * puis redirige vers la bonne action avec ses paramètres préremplis
 * (ex. la durée pour le plan de plaidoirie) via l'état de navigation.
 */

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { intention as intentionApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { ROUTES_PAR_ACTION } from "@/config/intentions";

export default function CommandBar() {
  const { t } = useTranslation();
  const [texte, setTexte] = useState("");
  const [enCours, setEnCours] = useState(false);
  const navigate = useNavigate();
  const dossierActifId = useAppStore((s) => s.dossierActifId);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const soumettre = async (e: FormEvent) => {
    e.preventDefault();
    const commande = texte.trim();
    if (!commande) return;

    if (dossierActifId === null) {
      pousserToast("info", t("commandBar.dossierRequis"));
      return;
    }

    setEnCours(true);
    try {
      const intention = await intentionApi.interpreterIntention(commande);
      if (intention.reformulation) pousserToast("info", intention.reformulation);

      const route = ROUTES_PAR_ACTION[intention.action];
      if (intention.confiance === "basse" || !route) {
        pousserToast("info", t("commandBar.intentionIncertaine"));
        return;
      }

      navigate(`/app${route}`, { state: intention.duree_minutes ? { dureeMinutesPreremplie: intention.duree_minutes } : undefined });
      setTexte("");
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("commandBar.erreurInterpretation"));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <form onSubmit={soumettre} className="flex items-center gap-3 border-b border-gold-600/10 bg-surface/40 px-4 py-2.5">
      <span className="text-gold-500" aria-hidden="true">
        💬
      </span>
      <input
        className="input flex-1 border-none bg-transparent px-0 focus-visible:shadow-none"
        placeholder={t("commandBar.placeholder")}
        value={texte}
        onChange={(e) => setTexte(e.target.value)}
        disabled={enCours}
      />
      <button type="submit" className="btn-secondary shrink-0 text-xs" disabled={enCours || !texte.trim()}>
        {enCours ? "…" : t("commandBar.envoyer")}
      </button>
    </form>
  );
}
