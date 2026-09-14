/**
 * ClePersonnelleForm — le formulaire "Utiliser ma propre clé Anthropic",
 * extrait de ClePersonnelleModal pour être réutilisable sans modale (voir
 * ParametresPage.tsx). La clé est stockée UNIQUEMENT dans sessionStorage de
 * ce navigateur (voir api/cleApiPersonnelle.ts) -- jamais envoyée ailleurs
 * qu'en en-tête X-Anthropic-Api-Key, jamais journalisée par le serveur (voir
 * le middleware dans backend/app/main.py), jamais persistée côté serveur.
 * Elle disparaît à la fermeture de l'onglet.
 */

import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "@/store/useAppStore";
import Button from "./Button";

interface ClePersonnelleFormProps {
  /** Copie d'intro adaptée au contexte d'affichage (bandeau démo vs page Paramètres). */
  introTexte?: string;
  onValide?: () => void;
}

export default function ClePersonnelleForm({ introTexte, onValide }: ClePersonnelleFormProps) {
  const { t } = useTranslation();
  const [cle, setCle] = useState("");
  const demoMode = useAppStore((s) => s.demoMode);
  const clePersonnelleActive = useAppStore((s) => s.clePersonnelleActive);
  const definirClePersonnelle = useAppStore((s) => s.definirClePersonnelle);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const introParDefaut = demoMode ? t("clePersonnelle.introDemo") : t("clePersonnelle.introHorsDemo");

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    if (!cle.trim()) return;
    definirClePersonnelle(cle.trim());
    pousserToast("success", t("clePersonnelle.enregistree"));
    setCle("");
    onValide?.();
  };

  const retirer = () => {
    definirClePersonnelle(null);
    pousserToast("info", demoMode ? t("clePersonnelle.retireeDemo") : t("clePersonnelle.retiree"));
  };

  if (clePersonnelleActive) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-risk-low/30 bg-risk-low/10 p-4">
        <p className="text-sm text-risk-low">✓ {t("clePersonnelle.active")}</p>
        <Button type="button" variant="ghost" onClick={retirer}>
          {t("clePersonnelle.retirerMaCle")}
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={soumettre} className="space-y-4">
      <p className="text-sm text-warmgray">{introTexte ?? introParDefaut}</p>
      <ul className="space-y-1 text-xs text-muted">
        <li>• {t("clePersonnelle.garantieStockage")}</li>
        <li>• {t("clePersonnelle.garantieEffacement")}</li>
        <li>• {t("clePersonnelle.garantieJournalisation")}</li>
      </ul>
      <div>
        <label htmlFor="cp-cle" className="mb-1.5 block text-sm text-warmgray">
          {t("clePersonnelle.champLabel")}
        </label>
        <input
          id="cp-cle"
          type="password"
          autoComplete="off"
          className="input font-mono"
          placeholder="sk-ant-api03-…"
          value={cle}
          onChange={(e) => setCle(e.target.value)}
        />
        <p className="mt-1.5 text-xs text-muted">
          {t("clePersonnelle.generezEnUne")}{" "}
          <a href="https://console.anthropic.com/" target="_blank" rel="noreferrer" className="text-amethyst-400 hover:underline">
            console.anthropic.com
          </a>
          .
        </p>
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <Button type="submit" variant="primary" disabled={!cle.trim()}>
          {t("clePersonnelle.activer")}
        </Button>
      </div>
    </form>
  );
}
