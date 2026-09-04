/**
 * ClePersonnelleModal — "Utiliser ma propre clé Anthropic". La clé est
 * stockée UNIQUEMENT dans sessionStorage de ce navigateur (voir
 * api/cleApiPersonnelle.ts) -- jamais envoyée ailleurs qu'en en-tête
 * X-Anthropic-Api-Key, jamais journalisée par le serveur (voir le
 * middleware dans backend/app/main.py), jamais persistée côté serveur.
 * Elle disparaît à la fermeture de l'onglet.
 */

import { useState, type FormEvent } from "react";
import { useAppStore } from "@/store/useAppStore";
import Modal from "./Modal";
import Button from "./Button";

interface ClePersonnelleModalProps {
  onFermer: () => void;
}

export default function ClePersonnelleModal({ onFermer }: ClePersonnelleModalProps) {
  const [cle, setCle] = useState("");
  const definirClePersonnelle = useAppStore((s) => s.definirClePersonnelle);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    if (!cle.trim()) return;
    definirClePersonnelle(cle.trim());
    pousserToast("success", "Clé personnelle enregistrée pour cette session — elle ne sera jamais journalisée par le serveur.");
    onFermer();
  };

  return (
    <Modal titre="Ma propre clé Anthropic" onFermer={onFermer} kicker="Sortir du mode démo">
      <form onSubmit={soumettre} className="space-y-4">
        <p className="text-sm text-warmgray">
          Indiquez votre propre clé API Anthropic pour obtenir des réponses générées en direct, avec votre propre quota, même si ce
          serveur public est en mode démo.
        </p>
        <ul className="space-y-1 text-xs text-muted">
          <li>• Stockée uniquement dans ce navigateur (sessionStorage) — jamais sur le serveur.</li>
          <li>• Effacée automatiquement à la fermeture de cet onglet.</li>
          <li>• Jamais journalisée : le serveur l'utilise pour vos requêtes sans jamais l'écrire nulle part.</li>
        </ul>
        <div>
          <label htmlFor="cp-cle" className="mb-1.5 block text-sm text-warmgray">
            Clé API (sk-ant-…)
          </label>
          <input
            id="cp-cle"
            type="password"
            autoComplete="off"
            className="input font-mono"
            placeholder="sk-ant-api03-…"
            value={cle}
            onChange={(e) => setCle(e.target.value)}
            autoFocus
          />
          <p className="mt-1.5 text-xs text-muted">
            Générez-en une sur{" "}
            <a href="https://console.anthropic.com/" target="_blank" rel="noreferrer" className="text-amethyst-400 hover:underline">
              console.anthropic.com
            </a>
            .
          </p>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onFermer}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" disabled={!cle.trim()}>
            Activer
          </Button>
        </div>
      </form>
    </Modal>
  );
}
