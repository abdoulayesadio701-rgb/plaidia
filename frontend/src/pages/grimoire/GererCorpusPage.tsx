/**
 * GererCorpusPage — /grimoire/corpus. Trois blocs :
 *  1. Importer un texte (OHADA, UE, Sénégal, CEDEAO, CEDH...) dans le corpus
 *     multi-source, non validé par défaut.
 *  2. Paramètres juridiques -- la juridiction active pour Consulter la
 *     jurisprudence et le Chat (Légifrance ou une source de corpus validée).
 *  3. Gérer le corpus -- tableau filtrable (source/pays/domaine),
 *     valider/rejeter chaque texte en attente.
 */

import { useState, type FormEvent } from "react";
import { jurisprudence as jurisprudenceApi } from "@/api";
import type { CorpusTexte } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { DOMAINES } from "@/config/domaines";
import { SOURCES_CORPUS, TYPES_TEXTE_CORPUS } from "@/config/corpus";
import Button from "@/components/Button";
import Tabs from "@/components/Tabs";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";

const ONGLETS = [
  { id: "attente", label: "En attente" },
  { id: "valide", label: "Validé" },
];

export default function GererCorpusPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <p className="kicker">Le Grimoire</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Gérer le corpus multi-source</h1>
        <p className="mt-2 text-sm text-warmgray">Textes juridiques hors Légifrance : OHADA, droit de l'Union européenne, droit sénégalais, CEDEAO, CEDH…</p>
      </div>

      <ImporterTexteSection />
      <ParametresJuridiquesSection />
      <GererCorpusSection />
    </div>
  );
}

function ImporterTexteSection() {
  const pousserToast = useAppStore((s) => s.pousserToast);
  const chargerCompteursAttente = useAppStore((s) => s.chargerCompteursAttente);
  const [ouvert, setOuvert] = useState(false);
  const [source, setSource] = useState(SOURCES_CORPUS[0]);
  const [sourceLibre, setSourceLibre] = useState("");
  const [pays, setPays] = useState("");
  const [typeTexte, setTypeTexte] = useState("");
  const [domaine, setDomaine] = useState("");
  const [reference, setReference] = useState("");
  const [dateTexte, setDateTexte] = useState("");
  const [contenu, setContenu] = useState("");
  const [enCours, setEnCours] = useState(false);

  const reinitialiser = () => {
    setSource(SOURCES_CORPUS[0]);
    setSourceLibre("");
    setPays("");
    setTypeTexte("");
    setDomaine("");
    setReference("");
    setDateTexte("");
    setContenu("");
  };

  const soumettre = async (e: FormEvent) => {
    e.preventDefault();
    const sourceFinale = source === "Autre" ? sourceLibre.trim() : source;
    if (!sourceFinale || !contenu.trim()) return;
    setEnCours(true);
    try {
      await jurisprudenceApi.importerTexteCorpus({
        source: sourceFinale,
        contenu: contenu.trim(),
        pays,
        type_texte: typeTexte,
        domaine,
        reference,
        date_texte: dateTexte,
      });
      pousserToast("success", "Texte importé — en attente de validation.");
      reinitialiser();
      setOuvert(false);
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "L'import a échoué.");
    } finally {
      setEnCours(false);
    }
  };

  return (
    <section className="card space-y-4 p-6">
      <button type="button" onClick={() => setOuvert((o) => !o)} className="flex w-full items-center justify-between text-left">
        <h2 className="font-serif text-h3 font-semibold text-gold-500">Importer un texte</h2>
        <span className={`text-warmgray transition-transform duration-200 ${ouvert ? "rotate-180" : ""}`} aria-hidden="true">
          ▾
        </span>
      </button>

      {ouvert && (
        <form onSubmit={soumettre} className="space-y-4 border-t border-gold-600/15 pt-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="it-source" className="mb-1.5 block text-sm text-warmgray">
                Source
              </label>
              <select id="it-source" className="input" value={source} onChange={(e) => setSource(e.target.value)}>
                {SOURCES_CORPUS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              {source === "Autre" && (
                <input
                  className="input mt-2"
                  placeholder="Nom de la source"
                  value={sourceLibre}
                  onChange={(e) => setSourceLibre(e.target.value)}
                />
              )}
            </div>
            <div>
              <label htmlFor="it-pays" className="mb-1.5 block text-sm text-warmgray">
                Pays (optionnel)
              </label>
              <input id="it-pays" className="input" value={pays} onChange={(e) => setPays(e.target.value)} />
            </div>
            <div>
              <label htmlFor="it-type" className="mb-1.5 block text-sm text-warmgray">
                Type de texte
              </label>
              <input id="it-type" list="it-types" className="input" value={typeTexte} onChange={(e) => setTypeTexte(e.target.value)} />
              <datalist id="it-types">
                {TYPES_TEXTE_CORPUS.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
            </div>
            <div>
              <label htmlFor="it-domaine" className="mb-1.5 block text-sm text-warmgray">
                Domaine
              </label>
              <input id="it-domaine" list="it-domaines" className="input" value={domaine} onChange={(e) => setDomaine(e.target.value)} />
              <datalist id="it-domaines">
                {DOMAINES.map((d) => (
                  <option key={d} value={d} />
                ))}
              </datalist>
            </div>
            <div>
              <label htmlFor="it-reference" className="mb-1.5 block text-sm text-warmgray">
                Référence
              </label>
              <input id="it-reference" className="input" placeholder="Ex. Acte uniforme OHADA du 15/12/2010" value={reference} onChange={(e) => setReference(e.target.value)} />
            </div>
            <div>
              <label htmlFor="it-date" className="mb-1.5 block text-sm text-warmgray">
                Date du texte
              </label>
              <input id="it-date" type="date" className="input" value={dateTexte} onChange={(e) => setDateTexte(e.target.value)} />
            </div>
          </div>
          <div>
            <label htmlFor="it-contenu" className="mb-1.5 block text-sm text-warmgray">
              Contenu
            </label>
            <textarea
              id="it-contenu"
              className="input min-h-[160px] resize-y"
              placeholder="Collez ici le texte intégral (ou l'extrait pertinent) du texte juridique."
              value={contenu}
              onChange={(e) => setContenu(e.target.value)}
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" variant="primary" loading={enCours} disabled={contenu.trim() === "" || (source === "Autre" && !sourceLibre.trim())}>
              Importer
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}

function ParametresJuridiquesSection() {
  const juridictionActive = useAppStore((s) => s.juridictionActive);
  const definirJuridictionActive = useAppStore((s) => s.definirJuridictionActive);
  const sourcesJuridictions = useAppStore((s) => s.sourcesJuridictions);

  return (
    <section className="card space-y-3 p-6">
      <h2 className="font-serif text-h3 font-semibold text-gold-500">Paramètres juridiques</h2>
      <p className="text-sm text-warmgray">
        La juridiction active détermine le contexte utilisé par l'agent pour « Consulter la jurisprudence » et le Chat. Seules les
        sources du corpus déjà validées apparaissent ici, en plus de Légifrance.
      </p>
      <select
        className="input max-w-sm"
        value={juridictionActive}
        onChange={(e) => void definirJuridictionActive(e.target.value)}
        aria-label="Juridiction active"
      >
        {sourcesJuridictions.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
    </section>
  );
}

function GererCorpusSection() {
  const pousserToast = useAppStore((s) => s.pousserToast);
  const chargerCompteursAttente = useAppStore((s) => s.chargerCompteursAttente);
  const chargerSourcesJuridictions = useAppStore((s) => s.chargerSourcesJuridictions);
  const [onglet, setOnglet] = useState("attente");
  const [source, setSource] = useState("");
  const [pays, setPays] = useState("");
  const [domaine, setDomaine] = useState("");
  const [ligneOuverte, setLigneOuverte] = useState<number | null>(null);
  const [idsEnCours, setIdsEnCours] = useState<Set<number>>(new Set());

  const { data: liste, loading, error, reload } = useAsync(
    () =>
      onglet === "attente"
        ? jurisprudenceApi.corpusEnAttente()
        : jurisprudenceApi.corpusValide({ source: source || undefined, pays: pays || undefined, domaine: domaine || undefined }),
    [onglet, source, pays, domaine]
  );

  const marquerEnCours = (id: number, actif: boolean) =>
    setIdsEnCours((s) => {
      const copie = new Set(s);
      if (actif) copie.add(id);
      else copie.delete(id);
      return copie;
    });

  const valider = async (item: CorpusTexte) => {
    marquerEnCours(item.id, true);
    try {
      await jurisprudenceApi.validerCorpus(item.id);
      pousserToast("success", `Texte « ${item.reference || item.source} » validé.`);
      reload();
      void chargerCompteursAttente();
      void chargerSourcesJuridictions();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "La validation a échoué.");
    } finally {
      marquerEnCours(item.id, false);
    }
  };

  const rejeter = async (item: CorpusTexte) => {
    marquerEnCours(item.id, true);
    try {
      await jurisprudenceApi.rejeterCorpus(item.id);
      pousserToast("success", `Texte « ${item.reference || item.source} » rejeté.`);
      reload();
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Le rejet a échoué.");
    } finally {
      marquerEnCours(item.id, false);
    }
  };

  return (
    <section className="space-y-4">
      <h2 className="font-serif text-h3 font-semibold text-gold-500">Le corpus</h2>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <Tabs tabs={ONGLETS} actif={onglet} onChange={setOnglet} />
        {onglet === "valide" && (
          <div className="flex flex-wrap gap-2">
            <select className="input w-auto" aria-label="Filtrer par source" value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="">Toutes les sources</option>
              {SOURCES_CORPUS.filter((s) => s !== "Autre").map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <input className="input w-auto" placeholder="Pays" aria-label="Filtrer par pays" value={pays} onChange={(e) => setPays(e.target.value)} />
            <select className="input w-auto" aria-label="Filtrer par domaine" value={domaine} onChange={(e) => setDomaine(e.target.value)}>
              <option value="">Tous les domaines</option>
              {DOMAINES.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading && <SkeletonList count={3} />}

      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && liste && liste.length === 0 && (
        <EmptyState
          titre={onglet === "attente" ? "Aucun texte en attente" : "Aucun texte validé"}
          description={onglet === "attente" ? "Utilisez « Importer un texte » ci-dessus pour en ajouter." : "Validez des textes en attente pour les voir apparaître ici."}
        />
      )}

      {!loading && !error && liste && liste.length > 0 && (
        <div className="space-y-2.5">
          {liste.map((item) => {
            const ouvert = ligneOuverte === item.id;
            return (
              <div key={item.id} className="card space-y-2 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ivory">{item.reference || "(sans référence)"}</p>
                    <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-warmgray">
                      <span>{item.source}</span>
                      {item.pays && <span>· {item.pays}</span>}
                      {item.type_texte && <span>· {item.type_texte}</span>}
                      {item.domaine && <span>· {item.domaine}</span>}
                      {item.date_texte && <span>· {item.date_texte}</span>}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <button onClick={() => setLigneOuverte(ouvert ? null : item.id)} className="text-xs text-amethyst-400 hover:underline">
                      {ouvert ? "Masquer" : "Lire"}
                    </button>
                    {onglet === "attente" && (
                      <>
                        <button
                          disabled={idsEnCours.has(item.id)}
                          onClick={() => void valider(item)}
                          className="rounded-md border border-risk-low/40 bg-risk-low/10 px-2.5 py-1 text-xs font-semibold text-risk-low transition-colors hover:bg-risk-low/20 disabled:opacity-40"
                        >
                          ✓ Valider
                        </button>
                        <button
                          disabled={idsEnCours.has(item.id)}
                          onClick={() => void rejeter(item)}
                          className="rounded-md border border-risk-high/40 bg-risk-high/10 px-2.5 py-1 text-xs font-semibold text-risk-high transition-colors hover:bg-risk-high/20 disabled:opacity-40"
                        >
                          ✕ Rejeter
                        </button>
                      </>
                    )}
                  </div>
                </div>
                {ouvert && (
                  <div className="max-h-64 overflow-y-auto rounded-md bg-surface-2 p-4">
                    <RichOutput texte={item.contenu} prose={false} className="text-sm" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
