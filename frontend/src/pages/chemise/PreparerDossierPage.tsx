/**
 * PreparerDossierPage — /chemise/preparer. Import de documents par
 * glisser-déposer (PDF, Word, Excel, image, texte) avec barre de
 * progression réelle par fichier (voir api/dossiers.ts::
 * importerDocumentAvecProgression), puis export des faits bruts accumulés
 * en Word. Chaque import ajoute son texte extrait aux faits du dossier
 * (extract.py côté serveur) -- c'est la même mécanique que « Analyser des
 * conclusions adverses », ici pensée pour plusieurs fichiers d'affilée.
 */

import { useCallback, useRef, useState, type DragEvent } from "react";
import { dossiers as dossiersApi, downloadBlob } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";

const EXTENSIONS_AUTORISEES = [".pdf", ".docx", ".xlsx", ".xls", ".txt", ".png", ".jpg", ".jpeg", ".webp"];
const EXTENSIONS_ACCEPT = EXTENSIONS_AUTORISEES.join(",");

type StatutFichier = "en_attente" | "en_cours" | "termine" | "erreur";

interface FichierSuivi {
  id: string;
  nom: string;
  taille: number;
  statut: StatutFichier;
  progression: number;
  erreur?: string;
  caracteresExtraits?: number;
  controller: AbortController;
}

function extensionAutorisee(nom: string): boolean {
  const idx = nom.lastIndexOf(".");
  if (idx === -1) return false;
  return EXTENSIONS_AUTORISEES.includes(nom.slice(idx).toLowerCase());
}

function formaterTaille(octets: number): string {
  if (octets < 1024) return `${octets} o`;
  if (octets < 1024 * 1024) return `${(octets / 1024).toFixed(0)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}

export default function PreparerDossierPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [fichiers, setFichiers] = useState<FichierSuivi[]>([]);
  const [survole, setSurvole] = useState(false);
  const [exportEnCours, setExportEnCours] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileQueue = useRef<Promise<void>>(Promise.resolve());

  const majFichier = useCallback((id: string, patch: Partial<FichierSuivi>) => {
    setFichiers((liste) => liste.map((f) => (f.id === id ? { ...f, ...patch } : f)));
  }, []);

  const traiterFichier = useCallback(
    async (suivi: FichierSuivi, fichier: File) => {
      if (!dossierActif) return;
      majFichier(suivi.id, { statut: "en_cours" });
      try {
        const resultat = await dossiersApi.importerDocumentAvecProgression(
          dossierActif.id,
          fichier,
          (pourcentage) => majFichier(suivi.id, { progression: pourcentage }),
          suivi.controller.signal
        );
        majFichier(suivi.id, { statut: "termine", progression: 100, caracteresExtraits: resultat.caracteres_extraits });
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") {
          majFichier(suivi.id, { statut: "erreur", erreur: "Import annulé." });
          return;
        }
        majFichier(suivi.id, { statut: "erreur", erreur: e instanceof Error ? e.message : "Échec de l'import." });
      }
    },
    [dossierActif, majFichier]
  );

  const ajouterFichiers = useCallback(
    (liste: FileList | File[]) => {
      const fichiersValides: { fichier: File; suivi: FichierSuivi }[] = [];
      for (const fichier of Array.from(liste)) {
        const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        if (!extensionAutorisee(fichier.name)) {
          setFichiers((l) => [
            ...l,
            {
              id,
              nom: fichier.name,
              taille: fichier.size,
              statut: "erreur",
              progression: 0,
              erreur: `Format non supporté (formats acceptés : ${EXTENSIONS_AUTORISEES.join(", ")}).`,
              controller: new AbortController(),
            },
          ]);
          continue;
        }
        const suivi: FichierSuivi = {
          id,
          nom: fichier.name,
          taille: fichier.size,
          statut: "en_attente",
          progression: 0,
          controller: new AbortController(),
        };
        fichiersValides.push({ fichier, suivi });
      }
      if (fichiersValides.length === 0) return;
      setFichiers((l) => [...l, ...fichiersValides.map((f) => f.suivi)]);
      // File d'attente séquentielle : le backend traite un fichier à la
      // fois, mieux vaut ne pas paralléliser plusieurs extractions lourdes.
      for (const { fichier, suivi } of fichiersValides) {
        fileQueue.current = fileQueue.current.then(() => traiterFichier(suivi, fichier));
      }
    },
    [traiterFichier]
  );

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setSurvole(false);
    if (e.dataTransfer.files.length) ajouterFichiers(e.dataTransfer.files);
  };

  const annulerFichier = (id: string) => {
    const cible = fichiers.find((f) => f.id === id);
    if (cible && cible.statut === "en_cours") cible.controller.abort();
  };

  const retirerFichier = (id: string) => setFichiers((liste) => liste.filter((f) => f.id !== id));

  const exporter = async () => {
    if (!dossierActif) return;
    setExportEnCours(true);
    try {
      const { blob, filename } = await dossiersApi.exporterFaitsBruts(dossierActif.id);
      downloadBlob(blob, filename ?? `${dossierActif.nom}_faits_bruts.docx`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'export.");
    } finally {
      setExportEnCours(false);
    }
  };

  if (!dossierActif) {
    return <EmptyState titre="Aucun dossier sélectionné" description="Sélectionnez ou créez un dossier pour y importer des documents." />;
  }

  const nombreTermines = fichiers.filter((f) => f.statut === "termine").length;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">La Chemise</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Préparer ce dossier</h1>
          <p className="mt-2 text-sm text-warmgray">Dossier actif : {dossierActif.nom}</p>
        </div>
        <Button variant="secondary" loading={exportEnCours} onClick={() => void exporter()}>
          ⬇ Exporter les faits bruts (Word)
        </Button>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setSurvole(true);
        }}
        onDragLeave={() => setSurvole(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={`flex cursor-pointer flex-col items-center gap-3 rounded-md border-2 border-dashed px-6 py-14 text-center transition-colors duration-150 ${
          survole ? "border-amethyst-400 bg-amethyst-400/10" : "border-gold-600/30 bg-surface hover:border-gold-500/50"
        }`}
      >
        <span className="text-3xl" aria-hidden="true">
          📥
        </span>
        <p className="font-serif text-h4 font-semibold text-ivory">Déposez vos documents ici</p>
        <p className="max-w-md text-sm text-warmgray">
          ou cliquez pour parcourir — PDF, Word, Excel, image ou texte. Chaque document importé est ajouté aux faits du dossier.
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={EXTENSIONS_ACCEPT}
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) ajouterFichiers(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {fichiers.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-warmgray">
              {nombreTermines}/{fichiers.length} document{fichiers.length > 1 ? "s" : ""} importé{nombreTermines > 1 ? "s" : ""}
            </p>
            <button onClick={() => setFichiers([])} className="text-xs text-muted hover:text-warmgray">
              Vider la liste
            </button>
          </div>
          <ul className="space-y-2.5">
            {fichiers.map((f) => (
              <li key={f.id} className="card space-y-2 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ivory">{f.nom}</p>
                    <p className="text-xs text-muted">
                      {formaterTaille(f.taille)}
                      {f.statut === "termine" && f.caracteresExtraits != null && ` · ${f.caracteresExtraits.toLocaleString("fr-FR")} caractères extraits`}
                      {f.statut === "erreur" && f.erreur && <span className="text-risk-high"> · {f.erreur}</span>}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {f.statut === "termine" && <span className="text-lg text-risk-low">✓</span>}
                    {f.statut === "erreur" && <span className="text-lg text-risk-high">⚠</span>}
                    {f.statut === "en_cours" && (
                      <button onClick={() => annulerFichier(f.id)} className="text-xs text-warmgray hover:text-ivory">
                        Annuler
                      </button>
                    )}
                    {f.statut !== "en_cours" && (
                      <button
                        onClick={() => retirerFichier(f.id)}
                        className="text-xs text-muted hover:text-ivory"
                        aria-label={`Retirer ${f.nom} de la liste`}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </div>
                {(f.statut === "en_cours" || f.statut === "en_attente") && (
                  <div className="h-1.5 w-full overflow-hidden rounded-pill bg-surface-3">
                    <div
                      className="h-full rounded-pill bg-amethyst-400 transition-all duration-200"
                      style={{ width: `${f.statut === "en_attente" ? 0 : f.progression}%` }}
                    />
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
