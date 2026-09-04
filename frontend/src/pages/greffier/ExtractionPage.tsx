/**
 * ExtractionPage — /greffier/extraction. Collage ou upload d'un document,
 * extraction en 5 blocs (dates, personnes et parties, références,
 * demandes, décisions). Indépendant de tout dossier (requiresDossier:
 * false, voir navigation.ts) -- le greffier traite des pièces avant même
 * qu'elles ne soient rattachées à une affaire.
 *
 * L'upload de fichier n'a de sens que si un dossier est actif : le seul
 * endpoint d'extraction de fichier côté backend (POST /dossiers/{id}/
 * documents) ajoute aussi le texte extrait aux faits de ce dossier -- même
 * contrainte et même bandeau explicatif que AnalyserConclusionsPage.
 */

import { useRef, useState } from "react";
import { dossiers as dossiersApi, greffier as greffierApi } from "@/api";
import type { ExtractionResultat } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

const EXTENSIONS_ACCEPTEES = ".pdf,.docx,.xlsx,.xls,.txt,.png,.jpg,.jpeg,.webp";

const BLOCS: { key: keyof ExtractionResultat; label: string; icone: string }[] = [
  { key: "dates", label: "Dates", icone: "📅" },
  { key: "personnes_et_parties", label: "Personnes et parties", icone: "👥" },
  { key: "references", label: "Références", icone: "🔖" },
  { key: "demandes", label: "Demandes", icone: "📌" },
  { key: "decisions", label: "Décisions", icone: "⚖" },
];

export default function ExtractionPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [texte, setTexte] = useState("");
  const [enImport, setEnImport] = useState(false);
  const inputFichierRef = useRef<HTMLInputElement>(null);

  const { data, loading, error, executer } = useLazyAction((t: string) => greffierApi.extraction(t));

  const importerFichier = async (fichier: File) => {
    if (!dossierActif) return;
    setEnImport(true);
    try {
      const resultat = await dossiersApi.importerDocument(dossierActif.id, fichier);
      setTexte((precedent) => (precedent ? `${precedent}\n\n${resultat.texte_extrait}` : resultat.texte_extrait));
      pousserToast(
        "success",
        `« ${resultat.nom_fichier} » importé (${resultat.caracteres_extraits.toLocaleString("fr-FR")} caractères) — également ajouté aux faits de « ${dossierActif.nom} ».`
      );
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'import du fichier.");
    } finally {
      setEnImport(false);
      if (inputFichierRef.current) inputFichierRef.current.value = "";
    }
  };

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
          className="input min-h-[220px] resize-y"
          placeholder="Collez ici le texte du document à traiter…"
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          disabled={loading || enImport}
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={inputFichierRef}
              type="file"
              accept={EXTENSIONS_ACCEPTEES}
              className="hidden"
              onChange={(e) => {
                const fichier = e.target.files?.[0];
                if (fichier) void importerFichier(fichier);
              }}
            />
            {dossierActif ? (
              <>
                <Button variant="secondary" loading={enImport} disabled={loading} onClick={() => inputFichierRef.current?.click()}>
                  📎 Importer un fichier
                </Button>
                <span className="text-xs text-muted">Le texte extrait sera aussi ajouté aux faits de « {dossierActif.nom} ».</span>
              </>
            ) : (
              <span className="text-xs text-muted">Sélectionnez un dossier dans le bandeau du haut pour aussi pouvoir importer un fichier.</span>
            )}
          </div>
          <Button variant="primary" loading={loading} disabled={!texte.trim() || enImport} onClick={lancer}>
            Extraire
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
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
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à extraire" description="Collez le texte du document ci-dessus, ou importez un fichier, puis cliquez sur « Extraire »." />
      )}
    </div>
  );
}
