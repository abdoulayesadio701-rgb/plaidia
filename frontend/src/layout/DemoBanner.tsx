/**
 * DemoBanner — bandeau "Mode démo" affiché tant que le serveur n'a pas de
 * clé Anthropic propre (voir GET /api/config, useAppStore::chargerConfiguration).
 * Bascule vers une confirmation discrète dès qu'une clé personnelle est
 * active pour cette session -- à partir de là, les requêtes DE CE VISITEUR
 * ne sont plus en mode démo (voir backend/app/demo.py::mode_demo_effectif),
 * même si le serveur, lui, reste en mode démo pour tout le monde d'autre.
 */

import { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import ClePersonnelleModal from "@/components/ClePersonnelleModal";

export default function DemoBanner() {
  const demoMode = useAppStore((s) => s.demoMode);
  const configurationChargee = useAppStore((s) => s.configurationChargee);
  const dossierDemoNom = useAppStore((s) => s.dossierDemoNom);
  const clePersonnelleActive = useAppStore((s) => s.clePersonnelleActive);
  const definirClePersonnelle = useAppStore((s) => s.definirClePersonnelle);
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [modalOuvert, setModalOuvert] = useState(false);

  if (!configurationChargee || !demoMode) return null;

  return (
    <>
      <div
        className={`flex shrink-0 flex-wrap items-center justify-center gap-x-3 gap-y-1 border-b px-4 py-2 text-center text-xs ${
          clePersonnelleActive ? "border-risk-low/30 bg-risk-low/10 text-risk-low" : "border-gold-500/30 bg-gold-500/10 text-gold-500"
        }`}
      >
        {clePersonnelleActive ? (
          <>
            <span>✓ Votre clé Anthropic personnelle est active pour cette session — réponses générées en direct, comme hors mode démo.</span>
            <button
              onClick={() => {
                definirClePersonnelle(null);
                pousserToast("info", "Clé personnelle retirée. Vous repassez en mode démo.");
              }}
              className="font-semibold underline underline-offset-2 hover:text-ivory"
            >
              Retirer ma clé
            </button>
          </>
        ) : (
          <>
            <span>
              🎭 <strong>Mode démo</strong> — les résultats sont des exemples préenregistrés
              {dossierDemoNom ? ` sur le dossier fictif « ${dossierDemoNom} »` : ""}, indépendants du texte saisi. Rien n'est conservé.
            </span>
            <button onClick={() => setModalOuvert(true)} className="font-semibold underline underline-offset-2 hover:text-ivory">
              Utiliser ma propre clé Anthropic
            </button>
          </>
        )}
      </div>

      {modalOuvert && <ClePersonnelleModal onFermer={() => setModalOuvert(false)} />}
    </>
  );
}
