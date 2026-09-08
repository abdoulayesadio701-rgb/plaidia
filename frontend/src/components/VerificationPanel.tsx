/**
 * VerificationPanel — rendu additif du bloc `verification` produit par le
 * pipeline multi-agents (garde-fou, vérificateur juridique, critique,
 * validation finale -- voir ARCHITECTURE_MULTI_AGENTS.md). Ne s'affiche
 * jamais si `verification` est absent (mode démo, ou fonctionnalité non
 * couverte par le pipeline complet) : composant purement additif, aucune
 * page appelante n'a besoin de le conditionner elle-même.
 *
 * Volontairement compact et non technique (§11/§12 de la demande) : un
 * statut de confiance + une synthèse en langage clair sont toujours
 * visibles ; le détail par affirmation et les critiques du contradicteur
 * restent repliés par défaut, pour ne jamais transformer le résultat en
 * tableau de bord de debug. La philosophie reste explicite dans le texte :
 * plusieurs contrôles indépendants aident à repérer les erreurs, ils ne
 * garantissent jamais une réponse correcte.
 */

import { useState } from "react";
import type { Critique, ElementVerifie, StatutConfiance, StatutVerification, Verification } from "@/api";
import RichOutput from "./RichOutput";

const BADGE_PAR_STATUT_GLOBAL: Record<string, { classe: string; icone: string; libelle: string }> = {
  VERIFIE: { classe: "badge-risk-low", icone: "✓", libelle: "Vérifié" },
  A_VERIFIER: { classe: "badge-risk-medium", icone: "⚠", libelle: "À vérifier" },
  INCERTAIN: { classe: "badge-risk-high", icone: "?", libelle: "Incertain" },
};

const BADGE_PAR_STATUT_ELEMENT: Record<string, { classe: string; icone: string }> = {
  VERIFIE: { classe: "badge-risk-low", icone: "✓" },
  PARTIELLEMENT_VERIFIE: { classe: "badge-risk-medium", icone: "⚠" },
  A_VERIFIER: { classe: "badge-risk-medium", icone: "⚠" },
  NON_VERIFIE: { classe: "badge-risk-high", icone: "?" },
};

function BadgeStatutGlobal({ statut }: { statut: StatutConfiance }) {
  const b = BADGE_PAR_STATUT_GLOBAL[statut] ?? { classe: "badge", icone: "?", libelle: statut };
  return (
    <span className={b.classe}>
      {b.icone} {b.libelle}
    </span>
  );
}

function BadgeStatutElement({ statut }: { statut: StatutVerification }) {
  const b = BADGE_PAR_STATUT_ELEMENT[statut] ?? { classe: "badge", icone: "?" };
  return <span className={`${b.classe} shrink-0`}>{b.icone} {statut.replace(/_/g, " ").toLowerCase()}</span>;
}

interface VerificationPanelProps {
  verification: Verification | null | undefined;
}

export default function VerificationPanel({ verification }: VerificationPanelProps) {
  const [detailsOuverts, setDetailsOuverts] = useState(false);
  if (!verification) return null;

  const { statut_global, elements, critiques, synthese_utilisateur } = verification;
  const aDesDetails = elements.length > 0 || critiques.length > 0;

  return (
    <div className="card space-y-3 border-amethyst-400/25 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold text-ivory">🔎 Vérification multi-agents</p>
        <BadgeStatutGlobal statut={statut_global} />
      </div>

      {synthese_utilisateur && <RichOutput texte={synthese_utilisateur} prose={false} className="text-sm" />}

      <p className="text-xs text-muted">
        Plusieurs contrôles indépendants (vérification des sources, contradicteur, validation finale) aident à repérer
        les erreurs et les incertitudes -- ils ne garantissent pas que cette analyse est exacte.
      </p>

      {aDesDetails && (
        <div>
          <button
            type="button"
            onClick={() => setDetailsOuverts((v) => !v)}
            className="text-xs font-medium text-amethyst-400 hover:underline"
          >
            {detailsOuverts ? "Masquer le détail" : "Voir le détail du contrôle"}
          </button>

          {detailsOuverts && (
            <div className="mt-3 space-y-4">
              {elements.length > 0 && (
                <div>
                  <p className="mb-1.5 text-micro font-medium uppercase tracking-wide text-warmgray">Affirmations contrôlées</p>
                  <ul className="space-y-2">
                    {elements.map((el: ElementVerifie, i: number) => (
                      <li key={i} className="flex items-start gap-2.5 rounded-md bg-surface-2/60 p-2.5 text-sm">
                        <BadgeStatutElement statut={el.statut} />
                        <div className="flex-1">
                          <p className="text-ivory">{el.affirmation}</p>
                          {el.commentaire && <p className="mt-0.5 text-xs text-warmgray">{el.commentaire}</p>}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {critiques.length > 0 && (
                <div>
                  <p className="mb-1.5 text-micro font-medium uppercase tracking-wide text-warmgray">
                    Faiblesses relevées par l'agent critique
                  </p>
                  <ul className="space-y-2">
                    {critiques.map((c: Critique, i: number) => (
                      <li key={i} className="rounded-md bg-surface-2/60 p-2.5 text-sm">
                        <p className="text-ivory">
                          <span className="font-medium">{c.cible}</span> — {c.commentaire}
                        </p>
                        <p className="mt-0.5 text-xs text-warmgray">Gravité : {c.gravite}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
