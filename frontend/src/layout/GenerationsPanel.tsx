/**
 * GenerationsPanel — liste déroulante des générations en arrière-plan
 * (voir useAppStore::generations, rafraîchi périodiquement par
 * AppLayout) -- portage web de gui.py::DialogueGenerations. Une
 * génération lancée depuis une page continue d'apparaître ici même après
 * avoir navigué ailleurs, jusqu'à suppression explicite confirmée.
 */

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Generation } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import ConfirmerModal from "@/components/ConfirmerModal";

interface GenerationsPanelProps {
  onFermer: () => void;
}

const ICONE_STATUT: Record<string, string> = { en_cours: "⏳", terminee: "✅", erreur: "⚠️" };

function formaterDate(iso: string, langue: string): string {
  const locale = langue === "en" ? "en-GB" : "fr-FR";
  return new Date(iso).toLocaleString(locale, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function GenerationsPanel({ onFermer }: GenerationsPanelProps) {
  const { t, i18n } = useTranslation();
  const conteneurRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const generations = useAppStore((s) => s.generations);
  const dossiers = useAppStore((s) => s.dossiers);
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const supprimerGenerationLocale = useAppStore((s) => s.supprimerGenerationLocale);
  const [aSupprimer, setASupprimer] = useState<Generation | null>(null);

  useEffect(() => {
    const onClickDehors = (e: MouseEvent) => {
      if (conteneurRef.current && !conteneurRef.current.contains(e.target as Node)) onFermer();
    };
    document.addEventListener("mousedown", onClickDehors);
    return () => document.removeEventListener("mousedown", onClickDehors);
  }, [onFermer]);

  const nomDossier = (id?: number | null) => dossiers.find((d) => d.id === id)?.nom ?? null;

  const ouvrirDossier = (generation: Generation) => {
    if (generation.dossier_id == null) return;
    if (dossiers.some((d) => d.id === generation.dossier_id)) selectionnerDossier(generation.dossier_id);
    navigate("/app/chemise/historique");
    onFermer();
  };

  const trie = [...generations].sort((a, b) => b.date_creation.localeCompare(a.date_creation));

  return (
    <>
      <div ref={conteneurRef} className="absolute right-0 top-full z-30 mt-2 w-96 rounded-md border border-gold-600/25 bg-surface-2 shadow-card">
        <div className="border-b border-gold-600/15 px-3 py-2">
          <p className="text-xs font-medium text-warmgray">{t("generationsPanel.titre")}</p>
        </div>
        <ul className="max-h-96 overflow-y-auto p-1">
          {trie.map((g) => {
            const dossier = nomDossier(g.dossier_id);
            return (
              <li key={g.id} className="rounded-md px-2.5 py-2 text-sm hover:bg-surface">
                <div className="flex items-start gap-2">
                  <span aria-hidden="true">{ICONE_STATUT[g.statut] ?? "•"}</span>
                  <div className="min-w-0 flex-1">
                    <button
                      onClick={() => ouvrirDossier(g)}
                      disabled={g.dossier_id == null}
                      className="block w-full truncate text-left text-ivory disabled:cursor-default"
                    >
                      {g.libelle}
                    </button>
                    <p className="text-xs text-warmgray">
                      {dossier ?? t("generationsPanel.sansDossier")} · {formaterDate(g.date_creation, i18n.language)}
                    </p>
                    {g.statut === "erreur" && g.erreur && <p className="mt-0.5 text-xs text-risk-high">{g.erreur}</p>}
                  </div>
                  <button
                    onClick={() => setASupprimer(g)}
                    className="shrink-0 rounded-md px-2 py-1 text-xs text-muted hover:text-risk-high"
                    title={t("generationsPanel.supprimer")}
                    aria-label={t("generationsPanel.supprimerAria", { libelle: g.libelle })}
                  >
                    ✕
                  </button>
                </div>
              </li>
            );
          })}
          {trie.length === 0 && <li className="px-2.5 py-3 text-sm text-warmgray">{t("generationsPanel.vide")}</li>}
        </ul>
      </div>

      {aSupprimer && (
        <ConfirmerModal
          titre={t("generationsPanel.confirmerTitre")}
          description={t("generationsPanel.confirmerDescription", { libelle: aSupprimer.libelle })}
          texteBouton={t("commun.supprimer")}
          onFermer={() => setASupprimer(null)}
          onConfirmer={async () => {
            await supprimerGenerationLocale(aSupprimer.id);
            setASupprimer(null);
          }}
        />
      )}
    </>
  );
}
