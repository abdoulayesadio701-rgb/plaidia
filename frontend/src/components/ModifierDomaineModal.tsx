/**
 * ModifierDomaineModal — changer le domaine d'un dossier existant (seul
 * champ modifiable après création côté backend, voir
 * PATCH /api/dossiers/{id}/domaine dans dossiers.py).
 */

import { useState } from "react";
import { dossiers as dossiersApi } from "@/api";
import type { Dossier } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { DOMAINES } from "@/config/domaines";
import { STADES_PROCEDURE, posturesPourDomaine } from "@/config/postures";
import Modal from "./Modal";
import Button from "./Button";

interface ModifierDomaineModalProps {
  dossier: Dossier;
  onFermer: () => void;
}

export default function ModifierDomaineModal({ dossier, onFermer }: ModifierDomaineModalProps) {
  const [domaine, setDomaine] = useState(dossier.domaine ?? "");
  const [partieRepresentee, setPartieRepresentee] = useState(dossier.partie_representee ?? "");
  const [stadeProcedure, setStadeProcedure] = useState(dossier.stade_procedure ?? "");
  const [objectif, setObjectif] = useState(dossier.objectif ?? "");
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const mettreAJourDossierLocal = useAppStore((s) => s.mettreAJourDossierLocal);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const soumettre = async () => {
    setEnCours(true);
    setErreur(null);
    try {
      const dossierMisAJour = await dossiersApi.modifierPosture(dossier.id, partieRepresentee, stadeProcedure, objectif.trim());
      mettreAJourDossierLocal(dossierMisAJour);
      pousserToast("success", `Posture du dossier « ${dossier.nom} » mise à jour.`);
      onFermer();
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "La mise à jour du domaine a échoué.");
    } finally {
      setEnCours(false);
    }
  };

  return (
    <Modal titre="Modifier le domaine" onFermer={onFermer} kicker={dossier.nom}>
      <div className="space-y-4">
        <div>
          <label htmlFor="md-domaine" className="mb-1.5 block text-sm text-warmgray">
            Domaine
          </label>
          <select id="md-domaine" className="input" value={domaine} onChange={(e) => setDomaine(e.target.value)} autoFocus>
            <option value="">— Non précisé —</option>
            {DOMAINES.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="md-partie" className="mb-1.5 block text-sm text-warmgray">Partie représentée</label>
          <select id="md-partie" className="input" value={partieRepresentee} onChange={(e) => setPartieRepresentee(e.target.value)}>
            <option value="">— Non précisée —</option>
            {posturesPourDomaine(domaine).map((partie) => <option key={partie} value={partie}>{partie}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="md-stade" className="mb-1.5 block text-sm text-warmgray">Stade</label>
          <select id="md-stade" className="input" value={stadeProcedure} onChange={(e) => setStadeProcedure(e.target.value)}>
            <option value="">— Non précisé —</option>
            {STADES_PROCEDURE.map((stade) => <option key={stade} value={stade}>{stade}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="md-objectif" className="mb-1.5 block text-sm text-warmgray">Objectif</label>
          <textarea id="md-objectif" className="input min-h-[80px] resize-y" value={objectif} onChange={(e) => setObjectif(e.target.value)} />
        </div>

        {erreur && <p className="text-sm text-risk-high">{erreur}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onFermer}>
            Annuler
          </Button>
          <Button type="button" variant="primary" loading={enCours} onClick={() => void soumettre()}>
            Enregistrer
          </Button>
        </div>
      </div>
    </Modal>
  );
}
