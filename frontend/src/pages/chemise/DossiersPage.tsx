/**
 * DossiersPage — /chemise/dossiers. Grille de tous les dossiers groupés par
 * domaine, recherche plein texte transversale (faits/parties/nom/domaine/
 * analyses, voir db.py::rechercher_dans_dossiers), création, modification
 * du domaine, suppression avec confirmation forte.
 */

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { dossiers as dossiersApi } from "@/api";
import type { Dossier } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import NouveauDossierModal from "@/components/NouveauDossierModal";
import ModifierDomaineModal from "@/components/ModifierDomaineModal";
import ConfirmerSuppressionModal from "@/components/ConfirmerSuppressionModal";
import PinButton from "@/components/PinButton";
import RechercheDossierResultats from "@/components/RechercheDossierResultats";
import { SkeletonBlock } from "@/components/Skeleton";
import justitiaPortrait from "@/assets/justitia-banniere.jpg";

function formaterDate(iso: string, langue: string): string {
  try {
    const locale = langue === "en" ? "en-GB" : "fr-FR";
    return new Date(iso).toLocaleDateString(locale, { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

export default function DossiersPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const dossiers = useAppStore((s) => s.dossiers);
  const dossiersCharges = useAppStore((s) => s.dossiersCharges);
  const dossiersErreur = useAppStore((s) => s.dossiersErreur);
  const chargerDossiers = useAppStore((s) => s.chargerDossiers);
  const selectionnerDossier = useAppStore((s) => s.selectionnerDossier);
  const retirerDossierLocal = useAppStore((s) => s.retirerDossierLocal);
  const pousserToast = useAppStore((s) => s.pousserToast);

  const [terme, setTerme] = useState("");
  const [modalCreation, setModalCreation] = useState(false);
  const [dossierAModifier, setDossierAModifier] = useState<Dossier | null>(null);
  const [dossierASupprimer, setDossierASupprimer] = useState<Dossier | null>(null);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);

  const {
    data: resultatsRecherche,
    loading: rechercheEnCours,
    error: rechercheErreur,
    executer: rechercher,
    reinitialiser: reinitialiserRecherche,
  } = useLazyAction((t: string) => dossiersApi.rechercherDossiers(t));

  useEffect(() => {
    if (!dossiersCharges) void chargerDossiers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const enRecherche = terme.trim().length > 0;

  useEffect(() => {
    if (!enRecherche) {
      reinitialiserRecherche();
      return;
    }
    const t = window.setTimeout(() => void rechercher(terme.trim()), 350);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terme]);

  const nonClasse = t("dossiersPage.nonClasse");
  const groupes = useMemo(() => {
    const parDomaine = new Map<string, Dossier[]>();
    for (const d of dossiers) {
      const cle = d.domaine?.trim() || nonClasse;
      if (!parDomaine.has(cle)) parDomaine.set(cle, []);
      parDomaine.get(cle)!.push(d);
    }
    return [...parDomaine.entries()].sort(([a], [b]) => (a === nonClasse ? 1 : b === nonClasse ? -1 : a.localeCompare(b)));
  }, [dossiers, nonClasse]);

  const ouvrirDossier = (id: number) => {
    selectionnerDossier(id);
    navigate("/app/chemise/historique");
  };

  const confirmerSuppression = async () => {
    if (!dossierASupprimer) return;
    setSuppressionEnCours(true);
    try {
      await dossiersApi.supprimerDossier(dossierASupprimer.id);
      retirerDossierLocal(dossierASupprimer.id);
      pousserToast("success", t("dossiersPage.supprime", { nom: dossierASupprimer.nom }));
      setDossierASupprimer(null);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("dossiersPage.echecSuppression"));
    } finally {
      setSuppressionEnCours(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{t("nav.sections.chemise")}</p>
          <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.chemise.dossiers")}</h1>
        </div>
        <Button variant="primary" onClick={() => setModalCreation(true)}>
          ＋ {t("nouveauDossier.titre")}
        </Button>
      </div>

      <input
        className="input max-w-xl"
        placeholder={t("dossiersPage.rechercherPlaceholder")}
        aria-label={t("dossiersPage.rechercherAria")}
        value={terme}
        onChange={(e) => setTerme(e.target.value)}
      />

      {enRecherche ? (
        <RechercheDossierResultats
          resultats={resultatsRecherche}
          loading={rechercheEnCours}
          erreur={rechercheErreur}
          terme={terme.trim()}
          onRelancer={() => void rechercher(terme.trim())}
          onOuvrir={ouvrirDossier}
        />
      ) : (
        <>
          {!dossiersCharges && !dossiersErreur && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="card space-y-3 p-5">
                  <SkeletonBlock className="h-5 w-3/4" />
                  <SkeletonBlock className="h-3.5 w-1/2" />
                  <SkeletonBlock className="h-3.5 w-1/3" />
                </div>
              ))}
            </div>
          )}

          {dossiersErreur && <ErrorState message={dossiersErreur} onRetry={() => void chargerDossiers()} />}

          {dossiersCharges && !dossiersErreur && dossiers.length === 0 && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,300px)_1fr]">
              <div className="portrait-card hidden aspect-[3/4] lg:block" aria-hidden="true">
                <img src={justitiaPortrait} alt="" />
                <div className="wash" />
                <div className="caption">
                  <p className="kicker">{t("dossiersPage.avantPremierDossier")}</p>
                  <p className="font-serif text-lg italic leading-snug text-ivory">
                    {t("dossiersPage.citation")}
                  </p>
                </div>
              </div>
              <EmptyState
                className="lg:h-full"
                titre={t("dossiersPage.aucunDossierTitre")}
                description={t("dossiersPage.aucunDossierDescription")}
                action={
                  <Button variant="primary" onClick={() => setModalCreation(true)}>
                    ＋ {t("nouveauDossier.titre")}
                  </Button>
                }
              />
            </div>
          )}

          {dossiersCharges &&
            !dossiersErreur &&
            groupes.map(([domaine, liste]) => (
              <div key={domaine} className="space-y-3">
                <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">
                  {domaine} <span className="text-muted">· {liste.length}</span>
                </p>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {liste.map((d) => (
                    <CarteDossier
                      key={d.id}
                      dossier={d}
                      onOuvrir={() => ouvrirDossier(d.id)}
                      onModifierDomaine={() => setDossierAModifier(d)}
                      onSupprimer={() => setDossierASupprimer(d)}
                      t={t}
                      langue={i18n.language}
                    />
                  ))}
                </div>
              </div>
            ))}
        </>
      )}

      {modalCreation && <NouveauDossierModal onFermer={() => setModalCreation(false)} />}
      {dossierAModifier && <ModifierDomaineModal dossier={dossierAModifier} onFermer={() => setDossierAModifier(null)} />}
      {dossierASupprimer && (
        <ConfirmerSuppressionModal
          titre={t("dossiersPage.supprimerCeDossier")}
          texteConfirmation={dossierASupprimer.nom}
          description={
            <p>
              {t("dossiersPage.confirmationSuppression1")} <strong className="text-ivory">{dossierASupprimer.nom}</strong>{" "}
              {t("dossiersPage.confirmationSuppression2")}
            </p>
          }
          enCours={suppressionEnCours}
          onFermer={() => setDossierASupprimer(null)}
          onConfirmer={confirmerSuppression}
        />
      )}
    </div>
  );
}

interface CarteDossierProps {
  dossier: Dossier;
  onOuvrir: () => void;
  onModifierDomaine: () => void;
  onSupprimer: () => void;
  t: TFunction;
  langue: string;
}

function CarteDossier({ dossier, onOuvrir, onModifierDomaine, onSupprimer, t, langue }: CarteDossierProps) {
  return (
    <div
      className="card-interactive space-y-3 p-5"
      onClick={onOuvrir}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOuvrir();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="font-serif text-h4 font-semibold text-ivory">{dossier.nom}</p>
        <span className="badge shrink-0 border-gold-600/30 bg-surface-2 text-warmgray">{t(`dossierStatut.${dossier.statut}`, dossier.statut)}</span>
      </div>
      {dossier.numero_dossier && <p className="text-xs text-muted">{t("dossiersPage.reference")} {dossier.numero_dossier}</p>}
      <div className="flex items-center justify-between gap-3 pt-1">
        <span className="text-xs text-warmgray">{formaterDate(dossier.date_creation, langue)}</span>
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <PinButton type="dossier" referenceId={dossier.id} libelle={dossier.nom} />
          <button
            onClick={onModifierDomaine}
            className="rounded-md px-2 py-1 text-xs text-gold-500 transition-colors hover:bg-surface-2"
            title={t("dossiersPage.modifierDomaine")}
          >
            ✎ {t("modifierDomaine.domaine")}
          </button>
          <button
            onClick={onSupprimer}
            className="rounded-md px-2 py-1 text-xs text-risk-high transition-colors hover:bg-risk-high/10"
            title={t("dossiersPage.supprimer")}
            aria-label={t("dossiersPage.supprimerCeDossierAria")}
          >
            🗑
          </button>
        </div>
      </div>
    </div>
  );
}

