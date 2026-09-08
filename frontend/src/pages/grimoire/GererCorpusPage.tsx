/**
 * GererCorpusPage — /grimoire/corpus. Deux blocs :
 *  1. Importer un texte (OHADA, UE, Sénégal, CEDEAO, CEDH...) dans le corpus
 *     multi-source, non validé par défaut.
 *  2. Gérer le corpus -- tableau filtrable (source/pays/domaine),
 *     valider/rejeter chaque texte en attente, valider en bloc par domaine.
 *
 * Le réglage de la juridiction active a déménagé dans ParametresPage.tsx --
 * c'est un réglage transversal (utilisé aussi par le Chat), pas propre au
 * Grimoire.
 */

import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { jurisprudence as jurisprudenceApi } from "@/api";
import type { CorpusTexte } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useAsync } from "@/hooks/useAsync";
import { DOMAINES } from "@/config/domaines";
import { SOURCES_CORPUS, TYPES_TEXTE_CORPUS } from "@/config/corpus";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import Tabs from "@/components/Tabs";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import RichOutput from "@/components/RichOutput";
import ConfirmerModal from "@/components/ConfirmerModal";
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
        <p className="mt-1 text-sm text-warmgray">
          Pour choisir la juridiction active (utilisée par le Chat et « Consulter la jurisprudence »), voir{" "}
          <Link to="/app/parametres" className="text-amethyst-400 hover:underline">
            Paramètres
          </Link>
          .
        </p>
      </div>

      <ImporterTexteSection />
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
  // Coller du texte reste la méthode historique (toujours utile pour un
  // extrait court) ; importer un fichier évite de recopier à la main un
  // acte uniforme ou un texte de plusieurs dizaines de pages déjà
  // disponible en PDF/DOCX (voir AUDIT_IMPORT_EXPORT.md).
  const [modeImport, setModeImport] = useState<"texte" | "fichier">("texte");

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

  const sourceFinale = source === "Autre" ? sourceLibre.trim() : source;
  const metaCommune = { source: sourceFinale, pays, type_texte: typeTexte, domaine, reference, date_texte: dateTexte };

  const soumettre = async (e: FormEvent) => {
    e.preventDefault();
    if (!sourceFinale || !contenu.trim()) return;
    setEnCours(true);
    try {
      await jurisprudenceApi.importerTexteCorpus({ ...metaCommune, contenu: contenu.trim() });
      pousserToast("success", "Texte importé – en attente de validation.");
      reinitialiser();
      setOuvert(false);
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "L'import a échoué.");
    } finally {
      setEnCours(false);
    }
  };

  const importerFichier = async (fichier: File) => {
    if (!sourceFinale) {
      pousserToast("error", "Renseignez d'abord la source avant d'importer un fichier.");
      return;
    }
    setEnCours(true);
    try {
      const resultat = await jurisprudenceApi.importerFichierCorpus(fichier, metaCommune);
      pousserToast("success", `« ${resultat.reference || fichier.name} » importé – en attente de validation.`);
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
            <div className="mb-2 flex w-fit rounded-md border border-gold-600/20 bg-surface-2 p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setModeImport("texte")}
                className={`rounded-md px-3 py-1.5 font-medium transition-colors ${modeImport === "texte" ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:text-ivory"}`}
              >
                Coller le texte
              </button>
              <button
                type="button"
                onClick={() => setModeImport("fichier")}
                className={`rounded-md px-3 py-1.5 font-medium transition-colors ${modeImport === "fichier" ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:text-ivory"}`}
              >
                Importer un fichier
              </button>
            </div>

            {modeImport === "texte" ? (
              <>
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
              </>
            ) : (
              <FileDropZone
                extensions={EXTENSIONS_DOCUMENT}
                loading={enCours}
                disabled={!sourceFinale}
                onFichiers={(fichiers) => void importerFichier(fichiers[0])}
                titre="Déposez le texte juridique ici"
                description="ou cliquez pour parcourir — PDF, Word, Excel, image ou texte. Renseignez d'abord la source ci-dessus."
              />
            )}
          </div>
          {modeImport === "texte" && (
            <div className="flex justify-end">
              <Button type="submit" variant="primary" loading={enCours} disabled={contenu.trim() === "" || (source === "Autre" && !sourceLibre.trim())}>
                Importer
              </Button>
            </div>
          )}
        </form>
      )}
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
  const [sourceAValiderEnBloc, setSourceAValiderEnBloc] = useState<{ source: string; domaine: string; nombre: number } | null>(null);
  const [validationBlocEnCours, setValidationBlocEnCours] = useState(false);

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

  // Regroupement par source PUIS par domaine, uniquement utile côté "En
  // attente" -- un import en masse (voir db.py::valider_texte_corpus_par_source)
  // peut mélanger des lots de qualité inégale au sein d'une même source (ex.
  // un acte uniforme mal océrisé parmi d'autres propres dans un import
  // OHADA) : le domaine (ex. le nom complet de l'acte) est le bon niveau de
  // granularité pour valider en bloc sans devoir faire confiance à toute la
  // source d'un coup.
  const groupesParSourceEtDomaine = useMemo(() => {
    if (onglet !== "attente" || !liste) return [];
    const parSource = new Map<string, Map<string, CorpusTexte[]>>();
    for (const item of liste) {
      if (!parSource.has(item.source)) parSource.set(item.source, new Map());
      const parDomaine = parSource.get(item.source)!;
      const cleDomaine = item.domaine || "(sans domaine précisé)";
      if (!parDomaine.has(cleDomaine)) parDomaine.set(cleDomaine, []);
      parDomaine.get(cleDomaine)!.push(item);
    }
    return [...parSource.entries()].map(([src, parDomaine]) => [src, [...parDomaine.entries()]] as const);
  }, [onglet, liste]);

  const confirmerValidationEnBloc = async () => {
    if (!sourceAValiderEnBloc) return;
    setValidationBlocEnCours(true);
    try {
      const { nombre_valide } = await jurisprudenceApi.validerCorpusParSource(
        sourceAValiderEnBloc.source,
        sourceAValiderEnBloc.domaine || undefined
      );
      const cible = sourceAValiderEnBloc.domaine ? `« ${sourceAValiderEnBloc.domaine} »` : `toute la source « ${sourceAValiderEnBloc.source} »`;
      pousserToast("success", `${nombre_valide} texte(s) validé(s) pour ${cible}.`);
      setSourceAValiderEnBloc(null);
      reload();
      void chargerCompteursAttente();
      void chargerSourcesJuridictions();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "La validation en bloc a échoué.");
    } finally {
      setValidationBlocEnCours(false);
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

      {!loading && !error && onglet === "attente" && groupesParSourceEtDomaine.length > 0 && (
        <div className="space-y-8">
          {groupesParSourceEtDomaine.map(([source, groupesDomaine]) => {
            const totalSource = groupesDomaine.reduce((n, [, items]) => n + items.length, 0);
            return (
              <div key={source} className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gold-600/20 pb-2">
                  <p className="text-sm font-semibold text-gold-500">
                    {source} <span className="font-normal text-warmgray">· {totalSource} en attente</span>
                  </p>
                  {groupesDomaine.length > 1 && totalSource > 1 && (
                    <button
                      onClick={() => setSourceAValiderEnBloc({ source, domaine: "", nombre: totalSource })}
                      className="text-xs text-warmgray underline decoration-dotted hover:text-ivory"
                      title="Valide tous les domaines de cette source en une fois – à réserver aux sources dont chaque lot est fiable"
                    >
                      Tout valider d'un coup ({totalSource})
                    </button>
                  )}
                </div>

                {groupesDomaine.map(([domaine, items]) => (
                  <div key={domaine} className="space-y-2.5">
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-md bg-surface-2/60 px-3 py-2">
                      <p className="text-sm font-medium text-ivory">
                        {domaine} <span className="text-warmgray">· {items.length}</span>
                      </p>
                      {items.length > 1 && (
                        <button
                          onClick={() => setSourceAValiderEnBloc({ source, domaine: domaine === "(sans domaine précisé)" ? "" : domaine, nombre: items.length })}
                          className="rounded-md border border-risk-low/40 bg-risk-low/10 px-2.5 py-1 text-xs font-semibold text-risk-low transition-colors hover:bg-risk-low/20"
                        >
                          ✓ Valider en bloc ({items.length})
                        </button>
                      )}
                    </div>
                    {items.map((item) => (
                      <LigneCorpus
                        key={item.id}
                        item={item}
                        ouvert={ligneOuverte === item.id}
                        enCours={idsEnCours.has(item.id)}
                        onToggleLire={() => setLigneOuverte(ligneOuverte === item.id ? null : item.id)}
                        onValider={() => void valider(item)}
                        onRejeter={() => void rejeter(item)}
                        afficherActions
                      />
                    ))}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {!loading && !error && onglet === "valide" && liste && liste.length > 0 && (
        <div className="space-y-2.5">
          {liste.map((item) => (
            <LigneCorpus
              key={item.id}
              item={item}
              ouvert={ligneOuverte === item.id}
              enCours={false}
              onToggleLire={() => setLigneOuverte(ligneOuverte === item.id ? null : item.id)}
              afficherActions={false}
            />
          ))}
        </div>
      )}

      {sourceAValiderEnBloc && (
        <ConfirmerModal
          titre="Valider en bloc"
          texteBouton="Valider en bloc"
          enCours={validationBlocEnCours}
          onFermer={() => setSourceAValiderEnBloc(null)}
          onConfirmer={confirmerValidationEnBloc}
          description={
            sourceAValiderEnBloc.domaine ? (
              <p>
                Tu confirmes faire confiance à <strong className="text-ivory">« {sourceAValiderEnBloc.domaine} »</strong> (source «{" "}
                {sourceAValiderEnBloc.source} ») : les <strong className="text-ivory">{sourceAValiderEnBloc.nombre}</strong> textes en
                attente de ce domaine précis deviennent immédiatement utilisables par l'agent en citation, sans relecture individuelle.
                Les autres domaines de cette même source, s'il y en a, restent en attente séparément.
              </p>
            ) : (
              <p>
                Tu confirmes faire confiance à <strong className="text-ivory">toute la source « {sourceAValiderEnBloc.source} »</strong>{" "}
                : les <strong className="text-ivory">{sourceAValiderEnBloc.nombre}</strong> textes en attente, tous domaines confondus,
                deviennent immédiatement utilisables par l'agent en citation, sans relecture individuelle. Réservé aux sources dont tu es
                sûr que <em>chaque</em> lot est fiable — pas un import dont certains sous-ensembles restent douteux.
              </p>
            )
          }
        />
      )}
    </section>
  );
}

interface LigneCorpusProps {
  item: CorpusTexte;
  ouvert: boolean;
  enCours: boolean;
  onToggleLire: () => void;
  onValider?: () => void;
  onRejeter?: () => void;
  afficherActions: boolean;
}

function LigneCorpus({ item, ouvert, enCours, onToggleLire, onValider, onRejeter, afficherActions }: LigneCorpusProps) {
  return (
    <div className="card space-y-2 p-4">
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
          <button onClick={onToggleLire} className="text-xs text-amethyst-400 hover:underline">
            {ouvert ? "Masquer" : "Lire"}
          </button>
          {afficherActions && (
            <>
              <button
                disabled={enCours}
                onClick={onValider}
                className="rounded-md border border-risk-low/40 bg-risk-low/10 px-2.5 py-1 text-xs font-semibold text-risk-low transition-colors hover:bg-risk-low/20 disabled:opacity-40"
              >
                ✓ Valider
              </button>
              <button
                disabled={enCours}
                onClick={onRejeter}
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
}
