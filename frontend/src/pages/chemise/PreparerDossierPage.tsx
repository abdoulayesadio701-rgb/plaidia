/**
 * PreparerDossierPage — /chemise/preparer. Import de documents par
 * glisser-déposer (PDF, Word, Excel, image, texte) avec barre de
 * progression réelle par fichier (voir api/dossiers.ts::
 * importerDocumentAvecProgression), puis export des faits bruts accumulés
 * en Word. Chaque import ajoute son texte extrait aux faits du dossier
 * (extract.py côté serveur) -- c'est la même mécanique que « Analyser des
 * conclusions adverses », ici pensée pour plusieurs fichiers d'affilée.
 *
 * Le glisser-déposer, le suivi par fichier et la liste de progression sont
 * fournis par FileDropZone / useImportFichiers / FileImportListe (voir
 * AUDIT_IMPORT_EXPORT.md) — cette page en a été le premier prototype,
 * depuis extrait en composants réutilisables ailleurs dans l'app.
 */

import { useState } from "react";
import { dossiers as dossiersApi, downloadBlob } from "@/api";
import { useAppStore, useDossierActif } from "@/store/useAppStore";
import { useImportFichiers } from "@/hooks/useImportFichiers";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import FileDropZone from "@/components/FileDropZone";
import FileImportListe from "@/components/FileImportListe";

export default function PreparerDossierPage() {
  const dossierActif = useDossierActif();
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [exportEnCours, setExportEnCours] = useState(false);

  const { fichiers, ajouterFichiers, annulerFichier, retirerFichier, viderListe } = useImportFichiers({
    extensionsAutorisees: EXTENSIONS_DOCUMENT,
    extraire: (fichier, onProgression, signal) =>
      dossiersApi.importerDocumentAvecProgression(dossierActif!.id, fichier, onProgression, signal),
  });

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

      <FileDropZone
        extensions={EXTENSIONS_DOCUMENT}
        multiple
        onFichiers={ajouterFichiers}
        titre="Déposez vos documents ici"
        description="ou cliquez pour parcourir — PDF, Word, Excel, image ou texte. Chaque document importé est ajouté aux faits du dossier."
      />

      <FileImportListe fichiers={fichiers} onAnnuler={annulerFichier} onRetirer={retirerFichier} onVider={viderListe} />
    </div>
  );
}
