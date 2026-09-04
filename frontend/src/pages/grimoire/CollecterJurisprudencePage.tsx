/**
 * CollecterJurisprudencePage — /grimoire/collecter. Interroge Judilibre par
 * mots-clés ; chaque décision trouvée est insérée en base NON validée (voir
 * POST /api/jurisprudence/collecter) -- rien n'est utilisable en citation
 * tant qu'un humain ne l'a pas validée dans « Gérer la jurisprudence ».
 */

import { useState } from "react";
import { jurisprudence as jurisprudenceApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { DOMAINES } from "@/config/domaines";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

export default function CollecterJurisprudencePage() {
  const chargerCompteursAttente = useAppStore((s) => s.chargerCompteursAttente);
  const [query, setQuery] = useState("");
  const [domaine, setDomaine] = useState("");

  const { data, loading, error, executer } = useLazyAction((q: string, d: string) => jurisprudenceApi.collecterJurisprudence(q, d));

  const lancer = async () => {
    await executer(query, domaine);
    void chargerCompteursAttente();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">Le Grimoire</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Collecter de la jurisprudence</h1>
        <p className="mt-2 text-sm text-warmgray">Recherche des décisions via Judilibre — chaque résultat reste en attente de validation manuelle.</p>
      </div>

      <div className="card space-y-4 p-6">
        <div>
          <label htmlFor="cj-query" className="mb-1.5 block text-sm text-warmgray">
            Mots-clés de recherche
          </label>
          <input
            id="cj-query"
            className="input"
            placeholder="Ex. licenciement faute grave absence injustifiée"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
        </div>
        <div>
          <label htmlFor="cj-domaine" className="mb-1.5 block text-sm text-warmgray">
            Domaine (optionnel)
          </label>
          <input id="cj-domaine" list="cj-domaines" className="input" value={domaine} onChange={(e) => setDomaine(e.target.value)} disabled={loading} />
          <datalist id="cj-domaines">
            {DOMAINES.map((d) => (
              <option key={d} value={d} />
            ))}
          </datalist>
        </div>
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} disabled={!query.trim()} onClick={() => void lancer()}>
            Collecter
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={3} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void lancer()} />}

      {!loading && !error && data && (
        <div className="space-y-4">
          <p className="text-sm text-warmgray">
            {data.nombre_collecte} décision{data.nombre_collecte > 1 ? "s" : ""} collectée{data.nombre_collecte > 1 ? "s" : ""}.
          </p>

          {data.decisions.length === 0 ? (
            <EmptyState titre="Aucune décision trouvée" description="Essayez d'autres mots-clés, ou élargissez la recherche." />
          ) : (
            <>
              <div className="space-y-3">
                {data.decisions.map((d, i) => (
                  <div key={i} className="card space-y-2 p-5">
                    <div className="flex items-start justify-between gap-3">
                      <p className="font-serif text-h4 font-semibold text-ivory">{d.reference}</p>
                      <span className="badge shrink-0 border-gold-500/30 bg-gold-500/10 text-gold-500">En attente</span>
                    </div>
                    <p className="text-sm text-warmgray">{d.resume}</p>
                    <div className="flex gap-2">
                      {d.domaine && <span className="text-xs text-muted">{d.domaine}</span>}
                      {d.source && <span className="text-xs text-muted">· {d.source}</span>}
                    </div>
                  </div>
                ))}
              </div>
              <p className="rounded-md border border-gold-500/30 bg-gold-500/10 p-4 text-sm text-gold-500">
                Rendez-vous dans « Gérer la jurisprudence » pour valider ou rejeter ces décisions avant de pouvoir les citer.
              </p>
            </>
          )}
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à collecter" description="Saisissez des mots-clés ci-dessus pour interroger Judilibre." />
      )}
    </div>
  );
}
