/**
 * GererJurisprudencePage — /grimoire/gerer. Valide ou rejette les
 * références collectées automatiquement (Judilibre) avant qu'elles ne
 * deviennent utilisables en citation. Le compteur de la Sidebar (badge sur
 * « Gérer la jurisprudence ») est rafraîchi après chaque action.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { jurisprudence as jurisprudenceApi } from "@/api";
import type { Jurisprudence } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { DOMAINES } from "@/config/domaines";
import Tabs from "@/components/Tabs";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import { SkeletonList } from "@/components/Skeleton";

export default function GererJurisprudencePage() {
  const { t } = useTranslation();
  const ONGLETS = [
    { id: "attente", label: t("gererJurisprudence.ongletAttente") },
    { id: "validee", label: t("gererJurisprudence.ongletValidee") },
  ];
  const pousserToast = useAppStore((s) => s.pousserToast);
  const chargerCompteursAttente = useAppStore((s) => s.chargerCompteursAttente);
  const [onglet, setOnglet] = useState("attente");
  const [domaineFiltre, setDomaineFiltre] = useState("");
  const [idsEnCours, setIdsEnCours] = useState<Set<number>>(new Set());

  const { data: liste, loading, error, reload } = useAsync(
    () => (onglet === "attente" ? jurisprudenceApi.jurisprudenceEnAttente(domaineFiltre || undefined) : jurisprudenceApi.jurisprudenceValidee(domaineFiltre || undefined)),
    [onglet, domaineFiltre]
  );

  const marquerEnCours = (id: number, actif: boolean) =>
    setIdsEnCours((s) => {
      const copie = new Set(s);
      if (actif) copie.add(id);
      else copie.delete(id);
      return copie;
    });

  const valider = async (item: Jurisprudence) => {
    marquerEnCours(item.id, true);
    try {
      await jurisprudenceApi.validerJurisprudence(item.id);
      pousserToast("success", t("gererJurisprudence.validee", { reference: item.reference }));
      reload();
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("gererJurisprudence.echecValidation"));
    } finally {
      marquerEnCours(item.id, false);
    }
  };

  const rejeter = async (item: Jurisprudence) => {
    marquerEnCours(item.id, true);
    try {
      await jurisprudenceApi.rejeterJurisprudence(item.id);
      pousserToast("success", t("gererJurisprudence.rejetee", { reference: item.reference }));
      reload();
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("gererJurisprudence.echecRejet"));
    } finally {
      marquerEnCours(item.id, false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="kicker">{t("nav.sections.grimoire")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.grimoire.gerer")}</h1>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <Tabs tabs={ONGLETS} actif={onglet} onChange={setOnglet} />
        <select className="input w-auto" aria-label={t("gererJurisprudence.filtrerParDomaine")} value={domaineFiltre} onChange={(e) => setDomaineFiltre(e.target.value)}>
          <option value="">{t("gererJurisprudence.tousLesDomaines")}</option>
          {DOMAINES.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      {loading && <SkeletonList count={3} />}

      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && liste && liste.length === 0 && (
        <EmptyState
          titre={onglet === "attente" ? t("gererJurisprudence.aucuneEnAttenteTitre") : t("gererJurisprudence.aucuneValideeTitre")}
          description={onglet === "attente" ? t("gererJurisprudence.aucuneEnAttenteDescription") : t("gererJurisprudence.aucuneValideeDescription")}
        />
      )}

      {!loading && !error && liste && liste.length > 0 && (
        <div className="overflow-x-auto rounded-md border border-gold-600/20">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-gold-600/20 bg-surface-2 text-left text-micro uppercase tracking-wide text-warmgray">
                <th className="px-4 py-3 font-medium">{t("collecterJurisprudence.reference")}</th>
                <th className="px-4 py-3 font-medium">{t("collecterJurisprudence.resume")}</th>
                <th className="px-4 py-3 font-medium">{t("modifierDomaine.domaine")}</th>
                <th className="px-4 py-3 font-medium">{t("collecterJurisprudence.source")}</th>
                {onglet === "attente" && <th className="px-4 py-3 font-medium">{t("collecterJurisprudence.actions")}</th>}
              </tr>
            </thead>
            <tbody>
              {liste.map((item) => (
                <tr key={item.id} className="border-b border-gold-600/10 last:border-0 hover:bg-surface-2/40">
                  <td className="px-4 py-3 font-medium text-ivory">{item.reference}</td>
                  <td className="max-w-sm px-4 py-3 text-warmgray">
                    <span className="line-clamp-2">{item.resume || "—"}</span>
                  </td>
                  <td className="px-4 py-3 text-warmgray">{item.domaine || "—"}</td>
                  <td className="max-w-[14rem] truncate px-4 py-3 text-warmgray">
                    {item.source ? (
                      <a
                        href={item.source}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={t("richOutput.ouvrirSource")}
                        className="text-gold-500 underline decoration-gold-600/50 underline-offset-2 transition-colors hover:text-gold-400"
                      >
                        {t("richOutput.consulterSource")}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  {onglet === "attente" && (
                    <td className="whitespace-nowrap px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          disabled={idsEnCours.has(item.id)}
                          onClick={() => void valider(item)}
                          className="rounded-md border border-risk-low/40 bg-risk-low/10 px-2.5 py-1 text-xs font-semibold text-risk-low transition-colors hover:bg-risk-low/20 disabled:opacity-40"
                        >
                          ✓ {t("gererJurisprudence.valider")}
                        </button>
                        <button
                          disabled={idsEnCours.has(item.id)}
                          onClick={() => void rejeter(item)}
                          className="rounded-md border border-risk-high/40 bg-risk-high/10 px-2.5 py-1 text-xs font-semibold text-risk-high transition-colors hover:bg-risk-high/20 disabled:opacity-40"
                        >
                          ✕ {t("gererJurisprudence.rejeter")}
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
