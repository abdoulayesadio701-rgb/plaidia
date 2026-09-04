/**
 * CommandBar — barre de commande en langage naturel, sous le header.
 * Reprend _commande_naturelle() de gui.py : appelle /api/intention,
 * puis redirige vers la bonne action avec ses paramètres préremplis
 * (ex. la durée pour le plan de plaidoirie) via l'état de navigation.
 */

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { intention as intentionApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";

const ROUTES_PAR_ACTION: Record<string, string> = {
  analyser: "/arsenal/analyser",
  resumer: "/arsenal/resumer",
  plan: "/arsenal/plan",
  simulateur: "/arsenal/simulateur",
  note: "/carnet/note",
};

export default function CommandBar() {
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
      pousserToast("info", "Sélectionnez ou créez un dossier avant de formuler une commande.");
      return;
    }

    setEnCours(true);
    try {
      const intention = await intentionApi.interpreterIntention(commande);
      if (intention.reformulation) pousserToast("info", intention.reformulation);

      const route = ROUTES_PAR_ACTION[intention.action];
      if (intention.confiance === "basse" || !route) {
        pousserToast("info", "Je ne suis pas certain d'avoir bien compris — utilisez la barre latérale, ou reformulez votre demande.");
        return;
      }

      navigate(`/app${route}`, { state: intention.duree_minutes ? { dureeMinutesPreremplie: intention.duree_minutes } : undefined });
      setTexte("");
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Impossible d'interpréter cette commande.");
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
        placeholder="Indiquez l'action souhaitée, par exemple : « analyser ces conclusions » ou « établir un plan de 10 minutes »…"
        value={texte}
        onChange={(e) => setTexte(e.target.value)}
        disabled={enCours}
      />
      <button type="submit" className="btn-secondary shrink-0 text-xs" disabled={enCours || !texte.trim()}>
        {enCours ? "…" : "Envoyer →"}
      </button>
    </form>
  );
}
