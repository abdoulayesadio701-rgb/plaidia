/**
 * ClassementPage — /greffier/classement. Classe un document selon sa
 * nature (assignation, jugement, ordonnance, conclusions, pièce, requête,
 * citation, procès-verbal, autre), avec une jauge de confiance et une
 * justification. Mêmes modalités de saisie (collage + upload conditionnel
 * au dossier actif) que ExtractionPage -- voir son en-tête pour le détail
 * de la contrainte backend.
 */

import { useRef, useState } from "react";
import { dossiers as dossiersApi, greffier as greffierApi } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import JaugeConfiance from "@/components/JaugeConfiance";
import { SkeletonList } from "@/components/Skeleton";

const EXTENSIONS_ACCEPTEES = ".pdf,.docx,.xlsx,.xls,.txt,.png,.jpg,.jpeg,.webp";

export default function ClassementPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [texte, setTexte] = useState("");
  const [enImport, setEnImport] = useState(false);
  const inputFichierRef = useRef<HTMLInputElement>(null);

  const { data, loading, error, executer } = useLazyAction((t: string) => greffierApi.classement(t));

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
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Classement automatique</h1>
        <p className="mt-2 text-sm text-warmgray">Identifie la nature d'un document (assignation, jugement, ordonnance, pièce…).</p>
      </div>

      <div className="card space-y-3 p-6">
        <textarea
          className="input min-h-[220px] resize-y"
          placeholder="Collez ici le texte du document à classer…"
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
            Classer
          </Button>
        </div>
      </div>

      {loading && <SkeletonList count={1} />}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
        <div className="card space-y-5 p-6">
          <div>
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">Nature du document</p>
            <p className="mt-1 font-serif text-h3 font-semibold capitalize text-gold-500">{data.nature}</p>
          </div>
          <JaugeConfiance niveau={data.confiance} />
          <div>
            <p className="mb-1 text-micro font-medium uppercase tracking-wide text-warmgray">Justification</p>
            <RichOutput texte={data.justification} prose={false} className="text-sm" />
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <EmptyState titre="Prêt à classer" description="Collez le texte du document ci-dessus, ou importez un fichier, puis cliquez sur « Classer »." />
      )}
    </div>
  );
}
