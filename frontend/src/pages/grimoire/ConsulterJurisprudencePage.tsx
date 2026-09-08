/**
 * ConsulterJurisprudencePage — /grimoire/jurisprudence. Question libre sur
 * la jurisprudence applicable, recherchée dans la juridiction active
 * (Légifrance en direct, ou un corpus validé -- voir la section
 * « Paramètres juridiques » de /grimoire/corpus pour la changer).
 */

import { useState } from "react";
import { jurisprudence as jurisprudenceApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";
import VerificationPanel from "@/components/VerificationPanel";

export default function ConsulterJurisprudencePage() {
  const juridictionActive = useAppStore((s) => s.juridictionActive);
  const [question, setQuestion] = useState("");
  const [but, setBut] = useState("");

  const { data, loading, error, executer, definirDonnees } = useLazyAction((q: string, b: string) =>
    jurisprudenceApi.consulterJurisprudence(q, b, juridictionActive)
  );

  const lancer = () => void executer(question, but);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">Le Grimoire</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Consulter la jurisprudence</h1>
        <p className="mt-2 flex items-center gap-2 text-sm text-warmgray">
          Juridiction active :
          <span className="badge border-amethyst-400/40 bg-amethyst-400/10 text-amethyst-400">{juridictionActive}</span>
        </p>
      </div>

      <div className="card space-y-4 p-6">
        <div>
          <label htmlFor="cj-question" className="mb-1.5 block text-sm text-warmgray">
            Situation ou question juridique
          </label>
          <textarea
            id="cj-question"
            className="input min-h-[140px] resize-y"
            placeholder="Ex. Un salarié peut-il être licencié pour avoir refusé une modification de son contrat de travail ?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
          />
        </div>
        <div>
          <label htmlFor="cj-but" className="mb-1.5 block text-sm text-warmgray">
            But de la recherche (optionnel)
          </label>
          <input
            id="cj-but"
            className="input"
            placeholder="Ex. décisions favorables à mon client"
            value={but}
            onChange={(e) => setBut(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="flex justify-end">
          <Button variant="primary" loading={loading} disabled={!question.trim()} onClick={lancer}>
            Consulter
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="card space-y-2 border-amethyst-400/30 p-5">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">Notions identifiées</p>
            <div className="flex flex-wrap gap-2">
              {data.notions.domaine && <span className="badge border-gold-600/30 bg-surface-2 text-gold-500">{data.notions.domaine}</span>}
              {data.notions.qualification_juridique && (
                <span className="badge border-gold-600/30 bg-surface-2 text-warmgray">{data.notions.qualification_juridique}</span>
              )}
            </div>
            {data.notions.mots_cles_recherche.length > 0 && (
              <p className="text-xs text-muted">Mots-clés : {data.notions.mots_cles_recherche.join(", ")}</p>
            )}
          </div>

          <div className="card p-6">
            <RichOutput texte={data.reponse} />
          </div>

          <VerificationPanel verification={data.verification} />

          <ChatContextuelPanel
            feature="jurisprudence_consultation"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            placeholder="Ex. « Explique cette décision plus en détail », « compare-la avec un arrêt plus récent »…"
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre="Prêt à consulter"
          description="Décrivez la situation ou la question juridique ci-dessus pour obtenir une réponse appuyée sur la juridiction active."
        />
      )}
    </div>
  );
}
