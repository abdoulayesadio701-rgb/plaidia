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
import { useTranslation } from "react-i18next";
import { greffier as greffierApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import RechercheDossierResultats from "@/components/RechercheDossierResultats";
import EmptyState from "@/components/EmptyState";

export default function RechercheTransversalePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const [terme, setTerme] = useState("");

  const { data, loading, error, executer, reinitialiser } = useLazyAction((texte: string) => greffierApi.rechercheTransversale(texte));

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
        <p className="kicker">{t("nav.espace.greffier")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.greffier.recherche")}</h1>
        <p className="mt-2 text-sm text-warmgray">{t("rechercheTransversale.sousTitre")}</p>
      </div>

      <input
        className="input"
        placeholder={t("rechercheTransversale.placeholder")}
        aria-label={t("nav.greffier.recherche")}
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
        <EmptyState titre={t("rechercheTransversale.saisirTitre")} description={t("rechercheTransversale.saisirDescription")} />
      )}
    </div>
  );
}
