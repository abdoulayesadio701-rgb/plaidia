/**
 * NouveauDossierModal — reprend les champs de DialogueNouveauDossier
 * (gui.py) : nom, numéro de référence, domaine, faits.
 */

import { useState, type FormEvent } from "react";
import { dossiers as dossiersApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { DOMAINES } from "@/config/domaines";
import Modal from "./Modal";
import Button from "./Button";

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
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const ajouterDossierLocal = useAppStore((s) => s.ajouterDossierLocal);
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const pousserToast = useAppStore((s) => s.pousserToast);

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
            id="nd-faits"
            className="input min-h-[100px] resize-y"
            value={faits}
            onChange={(e) => setFaits(e.target.value)}
          />
        </div>

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
