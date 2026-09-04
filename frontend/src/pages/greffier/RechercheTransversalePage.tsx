/**
 * RechercheTransversalePage — /greffier/recherche. Recherche plein texte
 * dans toutes les affaires (POST /api/greffier/recherche, même moteur que
 * la recherche de La Chemise -- voir RechercheDossierResultats, partagé
 * entre les deux). Un résultat ouvert sélectionne le dossier et mène à sa
 * fiche (La Chemise reste le seul écran de détail d'un dossier, quel que
 * soit l'espace d'où on y arrive).
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { greffier as greffierApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import RechercheDossierResultats from "@/components/RechercheDossierResultats";
import EmptyState from "@/components/EmptyState";

export default function RechercheTransversalePage() {
  const navigate = useNavigate();
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const [terme, setTerme] = useState("");

  const { data, loading, error, executer, reinitialiser } = useLazyAction((t: string) => greffierApi.rechercheTransversale(t));

  const enRecherche = terme.trim().length > 0;

  useEffect(() => {
    if (!enRecherche) {
      reinitialiser();
      return;
    }
    const t = window.setTimeout(() => void executer(terme.trim()), 350);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terme]);

  const ouvrirDossier = (id: number) => {
    selectionnerDossier(id);
    navigate("/app/chemise/historique");
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="kicker">Le Greffier</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Rechercher dans toutes les affaires</h1>
        <p className="mt-2 text-sm text-warmgray">Recherche transversale dans les faits, parties, noms, domaines et analyses de tous les dossiers.</p>
      </div>

      <input
        className="input"
        placeholder="Rechercher un nom, une référence, un mot-clé…"
        aria-label="Rechercher dans toutes les affaires"
        value={terme}
        onChange={(e) => setTerme(e.target.value)}
        autoFocus
      />

      {enRecherche ? (
        <RechercheDossierResultats
          resultats={data}
          loading={loading}
          erreur={error}
          terme={terme.trim()}
          onRelancer={() => void executer(terme.trim())}
          onOuvrir={ouvrirDossier}
        />
      ) : (
        <EmptyState titre="Saisissez un terme de recherche" description="La recherche porte sur l'ensemble des affaires, tous espaces confondus." />
      )}
    </div>
  );
}
