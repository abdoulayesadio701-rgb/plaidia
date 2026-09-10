/**
 * ExtractionPage — /greffier/extraction. Collage ou import d'un document,
 * extraction en 5 blocs (dates, personnes et parties, références,
 * demandes, décisions). Indépendant de tout dossier (requiresDossier:
 * false, voir navigation.ts) -- le greffier traite des pièces avant même
 * qu'elles ne soient rattachées à une affaire.
 *
 * L'import de fichier (voir useImportTexte) fonctionne avec ou sans
 * dossier actif : quand il y en a un, le texte extrait est aussi ajouté à
 * ses faits (importerDocument) ; sinon, extraction seule (extraireFichier).
 */

import { useState } from "react";
import { greffier as greffierApi } from "@/api";
import type { ExtractionResultat } from "@/api";
import { useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { useImportTexte } from "@/hooks/useImportTexte";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import ChoixImportModal from "@/components/ChoixImportModal";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

const BLOCS: { key: keyof ExtractionResultat; label: string; icone: string }[] = [
  { key: "dates", label: "Dates", icone: "📅" },
  { key: "personnes_et_parties", label: "Personnes et parties", icone: "👥" },
  { key: "references", label: "Références", icone: "🔖" },
  { key: "demandes", label: "Demandes", icone: "📌" },
  { key: "decisions", label: "Décisions", icone: "⚖" },
];

export default function ExtractionPage() {
  const dossierActif = useDossierActif();
  const [texte, setTexte] = useState("");

  const { data, loading, error, executer, definirDonnees } = useLazyAction((t: string) => greffierApi.extraction(t));
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: dossierActif?.id ?? null,
    getTexteActuel: () => texte,
    onTexteExtrait: setTexte,
  });

  const lancer = () => void executer(texte);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">Le Greffier</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Extraction d'éléments clés</h1>
        <p className="mt-2 text-sm text-warmgray">Repère dates, personnes, références, demandes et décisions dans un document.</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          {...dragProps}
          className={`input min-h-[220px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
          placeholder="Collez ici le texte du document à traiter, ou déposez un fichier…"
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
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={lancer}>
            Extraire
          </Button>
        </div>
      </div>

      {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {BLOCS.map(({ key, label, icone }) => {
              const items = data[key];
              return (
                <div key={key} className="card space-y-2.5 p-5">
                  <p className="font-serif text-h4 font-semibold text-ivory">
                    {icone} {label}
                  </p>
                  {items.length === 0 ? (
                    <p className="text-sm text-muted">Rien détecté.</p>
                  ) : (
                    <ul className="space-y-1.5 text-sm text-ivory">
                      {items.map((item, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-gold-500">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>

          <ChatContextuelPanel
            feature="extraction"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            dossierId={dossierActif?.id}
            placeholder="Ex. « Cherche aussi les délais de prescription », « ajoute cette date : … »…"
          />
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à extraire" description="Collez le texte du document ci-dessus, ou importez un fichier, puis cliquez sur « Extraire »." />
      )}
    </div>
  );
}
