/**
 * AnalyseStylePage — /arsenal/style. Ne nécessite pas de dossier actif
 * (voir navigation.ts, requiresDossier: false) — analyse rhétorique d'un
 * texte collé, indépendante d'un dossier précis.
 */

import { useState } from "react";
import { analyse as analyseApi } from "@/api";
import type { StyleResultat } from "@/api";
import { useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useImportTexte } from "@/hooks/useImportTexte";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import ChoixImportModal from "@/components/ChoixImportModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

type CleSection = "langage_de_couverture" | "affirmations_absolues" | "voix_passive_suspecte" | "ruptures_registre";

const SECTIONS: { key: CleSection; label: string; icone: string }[] = [
  { key: "langage_de_couverture", label: "Langage de couverture (hedging)", icone: "🗣️" },
  { key: "affirmations_absolues", label: "Affirmations absolues risquées", icone: "⚠️" },
  { key: "voix_passive_suspecte", label: "Voix passive suspecte", icone: "👤" },
  { key: "ruptures_registre", label: "Ruptures de registre", icone: "📉" },
];

export default function AnalyseStylePage() {
  const dossierActif = useDossierActif();
  const [texte, setTexte] = useState("");

  const { data, loading, error, executer, definirDonnees } = useLazyAction((t: string) => analyseApi.analyserStyle(t));
  // Page indépendante de tout dossier (requiresDossier: false) -- un dossier
  // actif reste optionnel : quand il y en a un, le texte extrait est aussi
  // ajouté à ses faits (importerDocument) ; sinon, extraction seule
  // (extraireFichier), sans rien écrire en base -- voir useImportTexte.
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: dossierActif?.id ?? null,
    getTexteActuel: () => texte,
    onTexteExtrait: setTexte,
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">L'Arsenal</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Analyse stylistique des conclusions adverses</h1>
        <p className="mt-2 text-sm text-warmgray">Analyse la manière dont le texte est rédigé — pas son contenu juridique.</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          {...dragProps}
          className={`input min-h-[220px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
          placeholder="Collez ici le texte des conclusions adverses à analyser, ou déposez un fichier…"
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          disabled={loading || enImport}
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <FileDropZone
              variante="compact"
              extensions={EXTENSIONS_DOCUMENT}
              multiple
              loading={enImport}
              disabled={loading}
              onFichiers={importerFichiers}
            />
            <span className="text-xs text-muted">
              {dossierActif
                ? `Le texte extrait sera aussi ajouté aux faits de « ${dossierActif.nom} ».`
                : "PDF, Word, Excel, image — le texte extrait est injecté ci-dessus."}
            </span>
          </div>
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={() => void executer(texte)}>
            Analyser le style
          </Button>
        </div>
      </div>

      {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

      {loading && <SkeletonList count={4} />}

      {!loading && error && <ErrorState message={error} onRetry={() => void executer(texte)} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <ResultatStyle data={data} />
          <ChatContextuelPanel
            feature="style"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            placeholder="Ex. « Pourquoi cette phrase est-elle une affirmation absolue risquée ? »…"
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState
          titre="Prêt à analyser"
          description="Collez le texte des conclusions adverses ci-dessus, ou importez un fichier, pour repérer les fragilités de leur rédaction."
        />
      )}
    </div>
  );
}

function ResultatStyle({ data }: { data: StyleResultat }) {
  return (
    <div className="space-y-5">
      {SECTIONS.map((section) => {
        const elements = data[section.key];
        return (
          <div key={section.key} className="card p-6">
            <p className="mb-3 font-serif text-h4 font-semibold text-ivory">
              {section.icone} {section.label}
            </p>
            {elements.length === 0 ? (
              <p className="text-sm text-muted">Rien de notable détecté.</p>
            ) : (
              <ul className="space-y-3">
                {elements.map((el, i) => (
                  <li key={i} className="border-l-2 border-gold-600/30 pl-3">
                    <p className="text-sm italic text-ivory">« {el.citation} »</p>
                    <RichOutput texte={el.commentaire} prose={false} className="mt-1 text-sm text-warmgray" />
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}

      {data.synthese_strategique && (
        <div className="card border-amethyst-400/30 p-6">
          <p className="mb-2 text-micro font-medium uppercase tracking-wide text-amethyst-400">💡 Synthèse stratégique</p>
          <RichOutput texte={data.synthese_strategique} />
        </div>
      )}

      <div className="rounded-md border border-gold-500/30 bg-gold-500/10 p-4 text-sm text-gold-500">
        ⚡ Outil de réflexion stratégique, pas une preuve juridique.
      </div>
    </div>
  );
}
