/**
 * VerificationProceduralePage — /greffier/verification-procedurale ET
 * /arsenal/verification-procedurale (voir router.tsx : les deux chemins
 * pointent vers ce même composant). Le prompt système a été neutralisé
 * côté backend pour servir aussi bien l'avocat que le greffier ("aide un
 * professionnel du droit, avocat ou greffier" -- voir analyse.py) : un
 * avocat en a tout autant besoin avant de déposer un acte ou plaider.
 *
 * Échéances avec un statut coloré (À venir / Proche / Possiblement
 * dépassée / Date incertaine -- voir VERIFICATION_PROCEDURALE_SYSTEM_PROMPT),
 * actes potentiellement manquants (le plus actionnable, en rouge), points
 * d'attention (plus doux, en doré -- même convention que PlanTimeline).
 */

import { greffier as greffierApi } from "@/api";
import { useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

const CLASSE_STATUT: Record<string, string> = {
  "À venir": "badge-risk-low",
  Proche: "badge-risk-medium",
  "Possiblement dépassée": "badge-risk-high",
};
const CLASSE_STATUT_DEFAUT = "badge border-muted/30 bg-surface-2 text-warmgray";

export default function VerificationProceduralePage() {
  const dossierActif = useDossierActif();
  const { data, loading, error, executer, definirDonnees } = useLazyAction(() => greffierApi.verificationProcedurale(dossierActif!.id));

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour vérifier sa procédure." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">Vérification procédurale</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Échéances et actes manquants</h1>
          <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
        </div>
        <Button variant="primary" loading={loading} onClick={() => void executer()}>
          {data ? "↻ Relancer la vérification" : "Vérifier la procédure"}
        </Button>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer()} />}

      {!loading && !error && data && (
        <div className="space-y-6">
          <div>
            <p className="mb-3 font-serif text-h3 font-semibold text-gold-500">Échéances identifiées</p>
            {data.echeances_identifiees.length === 0 ? (
              <p className="text-sm text-muted">Aucune échéance identifiée.</p>
            ) : (
              <div className="space-y-2.5">
                {data.echeances_identifiees.map((ech, i) => (
                  <div key={i} className="card flex flex-wrap items-center justify-between gap-3 p-4">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-ivory">{ech.echeance}</p>
                      <p className="text-xs text-muted">{ech.date}</p>
                    </div>
                    <span className={CLASSE_STATUT[ech.statut] ?? CLASSE_STATUT_DEFAUT}>{ech.statut}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {data.actes_potentiellement_manquants.length > 0 && (
            <div className="rounded-md border border-risk-high/30 bg-risk-high/10 p-5">
              <p className="mb-2 text-sm font-semibold text-risk-high">⚠ Actes potentiellement manquants</p>
              <ul className="space-y-1.5">
                {data.actes_potentiellement_manquants.map((a, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ivory">
                    <span className="text-risk-high">•</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.points_attention.length > 0 && (
            <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-5">
              <p className="mb-2 text-sm font-semibold text-gold-500">Points d'attention</p>
              <ul className="space-y-1.5">
                {data.points_attention.map((p, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ivory">
                    <span className="text-gold-500">•</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <ChatContextuelPanel
            feature="verification_procedurale"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif.id}
            placeholder="Ex. « Pourquoi cette échéance est-elle possiblement dépassée ? »…"
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre="Prêt à vérifier"
          description="Cliquez sur « Vérifier la procédure » pour repérer les échéances, actes manquants et points d'attention de ce dossier."
        />
      )}
    </div>
  );
}
