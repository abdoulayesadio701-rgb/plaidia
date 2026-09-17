/**
 * Sidebar — reprend panneau_gauche de gui.py : sélecteur d'espace
 * (Avocat / Greffier), puis la liste des sections de l'espace actif.
 * Repliable (icônes seules) via useAppStore.sidebarReplie -- desktop
 * uniquement (≥768px, breakpoint Tailwind `md`).
 *
 * Sous 768px, comportement distinct : tiroir (drawer) caché par défaut,
 * ouvert par-dessus le contenu via le bouton hamburger de TopBar (voir
 * useAppStore.sidebarMobileOuverte), avec overlay -- jamais de repli en
 * rail d'icônes sur mobile (sidebarReplie n'y a plus d'effet, un rail
 * d'icônes n'a pas de sens pour un tiroir déjà en superposition). Classes
 * non préfixées = mobile (mobile-first Tailwind) ; `md:` = desktop,
 * comportement inchangé.
 *
 * Une action qui exige un dossier (`requiresDossier`) est désactivée avec
 * un Tooltip tant qu'aucun dossier n'est actif — équivalent du
 * `_bouton_sidebar(..., besoin_dossier=True)` de gui.py, qui grisait le
 * bouton jusqu'à sélection d'un dossier.
 */

import { useEffect } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ESPACE_LABELS, NAVIGATION, navKey, type Espace } from "@/config/navigation";
import { useAppStore } from "@/store/useAppStore";
import Tooltip from "@/components/Tooltip";
import justitiaSignature from "@/assets/justitia-banniere.jpg";

const ESPACES: Espace[] = ["avocat", "greffier"];

/** Chemins qui affichent le compteur "en attente" du Grimoire (voir
 * useAppStore::chargerCompteursAttente, rafraîchi après chaque
 * valider/rejeter/collecter/importer). */
const COMPTEURS_PAR_CHEMIN: Record<string, keyof Pick<ReturnType<typeof useAppStore.getState>, "jurisprudenceEnAttenteCount" | "corpusEnAttenteCount">> = {
  "/grimoire/gerer": "jurisprudenceEnAttenteCount",
  "/grimoire/corpus": "corpusEnAttenteCount",
};

export default function Sidebar() {
  const { t } = useTranslation();
  const espaceActif = useAppStore((s) => s.espaceActif);
  const definirEspace = useAppStore((s) => s.definirEspace);
  const dossierActifId = useAppStore((s) => s.dossierActifId);
  const sidebarReplie = useAppStore((s) => s.sidebarReplie);
  const basculerSidebar = useAppStore((s) => s.basculerSidebar);
  const sidebarMobileOuverte = useAppStore((s) => s.sidebarMobileOuverte);
  const fermerSidebarMobile = useAppStore((s) => s.fermerSidebarMobile);
  const jurisprudenceEnAttenteCount = useAppStore((s) => s.jurisprudenceEnAttenteCount);
  const corpusEnAttenteCount = useAppStore((s) => s.corpusEnAttenteCount);

  const sections = NAVIGATION[espaceActif];
  const aUnDossier = dossierActifId !== null;
  const compteurs = { jurisprudenceEnAttenteCount, corpusEnAttenteCount };

  // Échap referme le tiroir mobile -- seulement branché tant qu'il est
  // ouvert, même convention que Modal.tsx.
  useEffect(() => {
    if (!sidebarMobileOuverte) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") fermerSidebarMobile();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [sidebarMobileOuverte, fermerSidebarMobile]);

  return (
    <>
      {/* Overlay mobile -- clic hors du tiroir referme, jamais affiché ≥768px
          (défensif : même si l'état restait "ouvert" après un redimensionnement). */}
      {sidebarMobileOuverte && (
        <div
          className="fixed inset-0 z-30 bg-void/70 backdrop-blur-[1px] md:hidden"
          onClick={fermerSidebarMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 flex-col border-r border-gold-600/15 bg-surface transition-transform duration-200 ease-out md:static md:inset-y-auto md:z-auto md:bg-surface/60 md:transition-all md:translate-x-0 ${
          sidebarMobileOuverte ? "translate-x-0" : "-translate-x-full"
        } ${sidebarReplie ? "md:w-16" : "md:w-72"}`}
      >
        <div className="flex items-center justify-between border-b border-gold-600/15 p-3">
          <p className={`px-1 text-micro text-warmgray ${sidebarReplie ? "md:hidden" : ""}`}>{t("sidebar.navigation")}</p>
          <button
            onClick={basculerSidebar}
            className="ml-auto hidden rounded-md p-1.5 text-warmgray transition-colors hover:bg-surface-2 hover:text-ivory md:inline-flex"
            aria-label={sidebarReplie ? t("sidebar.deplierAria") : t("sidebar.replierAria")}
            title={sidebarReplie ? t("sidebar.deplier") : t("sidebar.replier")}
          >
            {sidebarReplie ? "»" : "«"}
          </button>
          <button
            onClick={fermerSidebarMobile}
            className="ml-auto rounded-md p-1.5 text-warmgray transition-colors hover:bg-surface-2 hover:text-ivory md:hidden"
            aria-label={t("sidebar.fermerMobileAria")}
          >
            ✕
          </button>
        </div>

      {/* Sélecteur d'espace */}
      <div className={`flex gap-1 p-2 ${sidebarReplie ? "flex-col" : ""}`}>
        {ESPACES.map((espace) => {
          const libelleEspace = t(`nav.espace.${espace}`, ESPACE_LABELS[espace]);
          return (
            <button
              key={espace}
              onClick={() => definirEspace(espace)}
              className={`flex-1 rounded-md px-2 py-2 text-sm font-semibold transition-colors ${
                espaceActif === espace ? "bg-gold-500 text-ink" : "text-warmgray hover:bg-surface-2 hover:text-ivory"
              }`}
              title={libelleEspace}
            >
              {sidebarReplie ? libelleEspace.slice(0, 2) : libelleEspace}
            </button>
          );
        })}
      </div>

      {/* Sections de l'espace actif */}
      <nav className="flex-1 overflow-y-auto px-2 pb-4">
        {sections.map((section) => (
          <div key={section.title} className="mt-4 first:mt-2">
            <p className={`px-2 pb-1.5 text-micro text-warmgray ${sidebarReplie ? "md:hidden" : ""}`}>
              {t(section.titleKey, section.title)}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const desactive = item.requiresDossier && !aUnDossier;
                const cleCompteur = COMPTEURS_PAR_CHEMIN[item.path];
                const compteur = cleCompteur ? compteurs[cleCompteur] : 0;
                const libelleItem = t(navKey(item.path), item.label);
                const lien = (
                  <NavLink
                    key={item.path}
                    to={`/app${item.path}`}
                    aria-disabled={desactive}
                    onClick={(e) => {
                      if (desactive) e.preventDefault();
                      // Sélectionner une action referme le tiroir mobile --
                      // sans effet sur desktop (fermerSidebarMobile n'y est
                      // jamais lu pour l'affichage).
                      else fermerSidebarMobile();
                    }}
                    className={({ isActive }) =>
                      `flex items-center justify-between gap-2 rounded-md px-2.5 py-2 text-sm transition-colors ${
                        desactive
                          ? "cursor-not-allowed text-muted"
                          : isActive
                            ? "bg-amethyst-400/15 text-amethyst-400"
                            : "text-ivory hover:bg-surface-2"
                      }`
                    }
                  >
                    <span className="truncate">{sidebarReplie ? libelleItem.slice(0, 1) : libelleItem}</span>
                    {!sidebarReplie && compteur > 0 && (
                      <span className="shrink-0 rounded-pill bg-amethyst-400 px-1.5 py-0.5 text-[.65rem] font-semibold leading-none text-ink">
                        {compteur}
                      </span>
                    )}
                  </NavLink>
                );
                return (
                  <li key={item.path}>
                    {desactive && !sidebarReplie ? (
                      <Tooltip label={t("sidebar.dossierRequis")} className="block">
                        {lien}
                      </Tooltip>
                    ) : (
                      lien
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {!sidebarReplie && (
        <div className="sidebar-signature">
          <span className="sidebar-signature-photo" aria-hidden="true">
            <img src={justitiaSignature} alt="" />
          </span>
          <p className="sidebar-signature-text">{t("sidebar.signature")}</p>
        </div>
      )}
      </aside>
    </>
  );
}
