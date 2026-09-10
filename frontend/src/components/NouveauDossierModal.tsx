/**
 * NouveauDossierModal — reprend les champs de DialogueNouveauDossier
 * (gui.py) : nom, numéro de référence, domaine, faits.
 */

import { useState, type FormEvent } from "react";
import { dossiers as dossiersApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useImportTexte } from "@/hooks/useImportTexte";
import { DOMAINES } from "@/config/domaines";
import { STADES_PROCEDURE, posturesPourDomaine } from "@/config/postures";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Modal from "./Modal";
import Button from "./Button";
import ChoixImportModal from "./ChoixImportModal";
import FileDropZone from "./FileDropZone";

interface NouveauDossierModalProps {
  onFermer: () => void;
  /** Appelé avec l'id du dossier créé, une fois la création réussie. */
  onCree?: (dossierId: number) => void;
  /** Nom pré-rempli (ex. depuis la recherche du DossierSelector sans résultat). */
  nomInitial?: string;
}

export default function NouveauDossierModal({ onFermer, onCree, nomInitial = "" }: NouveauDossierModalProps) {
  const [nom, setNom] = useState(nomInitial);
  const [numeroDossier, setNumeroDossier] = useState("");
  const [domaine, setDomaine] = useState("");
  const [faits, setFaits] = useState("");
  const [partieRepresentee, setPartieRepresentee] = useState("");
  const [stadeProcedure, setStadeProcedure] = useState("");
  const [objectif, setObjectif] = useState("");
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const ajouterDossierLocal = useAppStore((s) => s.ajouterDossierLocal);
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const pousserToast = useAppStore((s) => s.pousserToast);
  // Pas encore de dossier à ce stade (formulaire de création) -- extraction
  // seule, rien n'est écrit en base avant la soumission (voir extraireFichier).
  const { enImport, survole, dragProps, importerFichiers, choixEnAttente, resoudreChoix } = useImportTexte({
    dossierId: null,
    getTexteActuel: () => faits,
    onTexteExtrait: setFaits,
  });

  const soumettre = async (e: FormEvent) => {
    e.preventDefault();
    if (!nom.trim()) {
      setErreur("Veuillez indiquer un nom pour ce dossier.");
      return;
    }
    setEnCours(true);
    setErreur(null);
    try {
      const dossier = await dossiersApi.creerDossier({
        nom: nom.trim(),
        numero_dossier: numeroDossier.trim(),
        domaine,
        faits: faits.trim(),
        partie_representee: partieRepresentee,
        stade_procedure: stadeProcedure,
        objectif: objectif.trim(),
      });
      ajouterDossierLocal(dossier);
      selectionnerDossier(dossier.id);
      pousserToast("success", `Dossier « ${dossier.nom} » créé.`);
      onCree?.(dossier.id);
      onFermer();
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "La création du dossier a échoué.");
    } finally {
      setEnCours(false);
    }
  };

  return (
    <Modal titre="Nouveau dossier" onFermer={onFermer}>
      <form onSubmit={soumettre} className="space-y-4">
        <div>
          <label htmlFor="nd-nom" className="mb-1.5 block text-sm text-warmgray">
            Nom du dossier
          </label>
          <input
            id="nd-nom"
            className="input"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
            autoFocus
            placeholder="Ex. Martin bail commercial"
          />
        </div>
        <div>
          <label htmlFor="nd-partie" className="mb-1.5 block text-sm text-warmgray">Partie représentée (optionnel)</label>
          <select id="nd-partie" className="input" value={partieRepresentee} onChange={(e) => setPartieRepresentee(e.target.value)}>
            <option value="">— Non précisée —</option>
            {posturesPourDomaine(domaine).map((partie) => <option key={partie} value={partie}>{partie}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="nd-stade" className="mb-1.5 block text-sm text-warmgray">Stade (optionnel)</label>
          <select id="nd-stade" className="input" value={stadeProcedure} onChange={(e) => setStadeProcedure(e.target.value)}>
            <option value="">— Non précisé —</option>
            {STADES_PROCEDURE.map((stade) => <option key={stade} value={stade}>{stade}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="nd-objectif" className="mb-1.5 block text-sm text-warmgray">Objectif (optionnel)</label>
          <textarea id="nd-objectif" className="input min-h-[80px] resize-y" value={objectif} onChange={(e) => setObjectif(e.target.value)} />
        </div>
        <div>
          <label htmlFor="nd-numero" className="mb-1.5 block text-sm text-warmgray">
            Numéro de référence (optionnel)
          </label>
          <input id="nd-numero" className="input" value={numeroDossier} onChange={(e) => setNumeroDossier(e.target.value)} />
        </div>
        <div>
          <label htmlFor="nd-domaine" className="mb-1.5 block text-sm text-warmgray">
            Domaine
          </label>
          <select id="nd-domaine" className="input" value={domaine} onChange={(e) => setDomaine(e.target.value)}>
            <option value="">— Non précisé —</option>
            {DOMAINES.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="nd-faits" className="mb-1.5 block text-sm text-warmgray">
            Faits (optionnel)
          </label>
          <textarea
            {...dragProps}
            id="nd-faits"
            className={`input min-h-[100px] resize-y ${survole ? "ring-2 ring-amethyst-400" : ""}`}
            placeholder="Décrivez les faits, ou déposez un fichier…"
            value={faits}
            onChange={(e) => setFaits(e.target.value)}
            disabled={enCours || enImport}
          />
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <FileDropZone
              variante="compact"
              extensions={EXTENSIONS_DOCUMENT}
              multiple
              loading={enImport}
              disabled={enCours}
              onFichiers={importerFichiers}
            />
            <span className="text-xs text-muted">PDF, Word, Excel, image — le texte extrait est injecté ci-dessus.</span>
          </div>
        </div>

        {choixEnAttente && <ChoixImportModal noms={choixEnAttente.noms} onChoisir={resoudreChoix} />}

        {erreur && <p className="text-sm text-risk-high">{erreur}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onFermer}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" loading={enCours}>
            Créer
          </Button>
        </div>
      </form>
    </Modal>
  );
}
