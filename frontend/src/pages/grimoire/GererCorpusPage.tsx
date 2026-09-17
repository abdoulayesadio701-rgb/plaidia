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
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
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

export default function GererCorpusPage() {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <p className="kicker">{t("nav.sections.grimoire")}</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">{t("nav.grimoire.corpus")}</h1>
        <p className="mt-2 text-sm text-warmgray">{t("gererCorpus.sousTitre")}</p>
        <p className="mt-1 text-sm text-warmgray">
          {t("gererCorpus.pourJuridiction")}{" "}
          <Link to="/app/parametres" className="text-amethyst-400 hover:underline">
            {t("topBar.parametres")}
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
  const { t } = useTranslation();
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
      pousserToast("success", t("gererCorpus.texteImporte"));
      reinitialiser();
      setOuvert(false);
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("gererCorpus.echecImport"));
    } finally {
      setEnCours(false);
    }
  };

  const importerFichier = async (fichier: File) => {
    if (!sourceFinale) {
      pousserToast("error", t("gererCorpus.sourceRequise"));
      return;
    }
    setEnCours(true);
    try {
      const resultat = await jurisprudenceApi.importerFichierCorpus(fichier, metaCommune);
      pousserToast("success", t("gererCorpus.fichierImporte", { nom: resultat.reference || fichier.name }));
      reinitialiser();
      setOuvert(false);
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("gererCorpus.echecImport"));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <section className="card space-y-4 p-6">
      <button type="button" onClick={() => setOuvert((o) => !o)} className="flex w-full items-center justify-between text-left">
        <h2 className="font-serif text-h3 font-semibold text-gold-500">{t("gererCorpus.importerTexte")}</h2>
        <span className={`text-warmgray transition-transform duration-200 ${ouvert ? "rotate-180" : ""}`} aria-hidden="true">
          ▾
        </span>
      </button>

      {ouvert && (
        <form onSubmit={soumettre} className="space-y-4 border-t border-gold-600/15 pt-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="it-source" className="mb-1.5 block text-sm text-warmgray">
                {t("gererCorpus.source")}
              </label>
              <select id="it-source" className="input" value={source} onChange={(e) => setSource(e.target.value)}>
                {SOURCES_CORPUS.map((s) => (
                  <option key={s} value={s}>
                    {t(`sourceCorpus.${s}`, s)}
                  </option>
                ))}
              </select>
              {source === "Autre" && (
                <input
                  className="input mt-2"
                  placeholder={t("gererCorpus.nomDeLaSource")}
                  value={sourceLibre}
                  onChange={(e) => setSourceLibre(e.target.value)}
                />
              )}
            </div>
            <div>
              <label htmlFor="it-pays" className="mb-1.5 block text-sm text-warmgray">
                {t("gererCorpus.paysOptionnel")}
              </label>
              <input id="it-pays" className="input" value={pays} onChange={(e) => setPays(e.target.value)} />
            </div>
            <div>
              <label htmlFor="it-type" className="mb-1.5 block text-sm text-warmgray">
                {t("gererCorpus.typeDeTexte")}
              </label>
              <input id="it-type" list="it-types" className="input" value={typeTexte} onChange={(e) => setTypeTexte(e.target.value)} />
              <datalist id="it-types">
                {TYPES_TEXTE_CORPUS.map((tt) => (
                  <option key={tt} value={tt} label={t(`typeTexteCorpus.${tt}`, tt)} />
                ))}
              </datalist>
            </div>
            <div>
              <label htmlFor="it-domaine" className="mb-1.5 block text-sm text-warmgray">
                {t("modifierDomaine.domaine")}
              </label>
              <input id="it-domaine" list="it-domaines" className="input" value={domaine} onChange={(e) => setDomaine(e.target.value)} />
              <datalist id="it-domaines">
                {DOMAINES.map((d) => (
                  <option key={d} value={d} label={t(`domaine.${d}`, d)} />
                ))}
              </datalist>
            </div>
            <div>
              <label htmlFor="it-reference" className="mb-1.5 block text-sm text-warmgray">
                {t("collecterJurisprudence.reference")}
              </label>
              <input id="it-reference" className="input" placeholder={t("gererCorpus.referencePlaceholder")} value={reference} onChange={(e) => setReference(e.target.value)} />
            </div>
            <div>
              <label htmlFor="it-date" className="mb-1.5 block text-sm text-warmgray">
                {t("gererCorpus.dateDuTexte")}
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
                {t("gererCorpus.collerLeTexte")}
              </button>
              <button
                type="button"
                onClick={() => setModeImport("fichier")}
                className={`rounded-md px-3 py-1.5 font-medium transition-colors ${modeImport === "fichier" ? "bg-amethyst-400/15 text-amethyst-400" : "text-warmgray hover:text-ivory"}`}
              >
                {t("fileDropZone.libelleBouton").replace("📎 ", "")}
              </button>
            </div>

            {modeImport === "texte" ? (
              <>
                <label htmlFor="it-contenu" className="mb-1.5 block text-sm text-warmgray">
                  {t("gererCorpus.contenu")}
                </label>
                <textarea
                  id="it-contenu"
                  className="input min-h-[160px] resize-y"
                  placeholder={t("gererCorpus.contenuPlaceholder")}
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
                titre={t("gererCorpus.deposezIci")}
                description={t("gererCorpus.dropzoneDescription")}
              />
            )}
          </div>
          {modeImport === "texte" && (
            <div className="flex justify-end">
              <Button type="submit" variant="primary" loading={enCours} disabled={contenu.trim() === "" || (source === "Autre" && !sourceLibre.trim())}>
                {t("gererCorpus.importer")}
              </Button>
            </div>
          )}
        </form>
      )}
    </section>
  );
}

function GererCorpusSection() {
  const { t } = useTranslation();
  const ONGLETS = [
    { id: "attente", label: t("gererJurisprudence.ongletAttente") },
    { id: "valide", label: t("gererCorpus.ongletValide") },
  ];
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
      pousserToast("success", t("gererCorpus.texteValide", { ref: item.reference || item.source }));
      reload();
      void chargerCompteursAttente();
      void chargerSourcesJuridictions();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("gererJurisprudence.echecValidation"));
    } finally {
      marquerEnCours(item.id, false);
    }
  };

  const rejeter = async (item: CorpusTexte) => {
    marquerEnCours(item.id, true);
    try {
      await jurisprudenceApi.rejeterCorpus(item.id);
      pousserToast("success", t("gererCorpus.texteRejete", { ref: item.reference || item.source }));
      reload();
      void chargerCompteursAttente();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("gererJurisprudence.echecRejet"));
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
  const sansDomainePrecise = t("gererCorpus.sansDomainePrecise");
  const groupesParSourceEtDomaine = useMemo(() => {
    if (onglet !== "attente" || !liste) return [];
    const parSource = new Map<string, Map<string, CorpusTexte[]>>();
    for (const item of liste) {
      if (!parSource.has(item.source)) parSource.set(item.source, new Map());
      const parDomaine = parSource.get(item.source)!;
      const cleDomaine = item.domaine || sansDomainePrecise;
      if (!parDomaine.has(cleDomaine)) parDomaine.set(cleDomaine, []);
      parDomaine.get(cleDomaine)!.push(item);
    }
    return [...parSource.entries()].map(([src, parDomaine]) => [src, [...parDomaine.entries()]] as const);
  }, [onglet, liste, sansDomainePrecise]);

  const confirmerValidationEnBloc = async () => {
    if (!sourceAValiderEnBloc) return;
    setValidationBlocEnCours(true);
    try {
      const { nombre_valide } = await jurisprudenceApi.validerCorpusParSource(
        sourceAValiderEnBloc.source,
        sourceAValiderEnBloc.domaine || undefined
      );
      pousserToast(
        "success",
        sourceAValiderEnBloc.domaine
          ? t("gererCorpus.blocValideDomaine", { count: nombre_valide, domaine: sourceAValiderEnBloc.domaine })
          : t("gererCorpus.blocValideSource", { count: nombre_valide, source: sourceAValiderEnBloc.source })
      );
      setSourceAValiderEnBloc(null);
      reload();
      void chargerCompteursAttente();
      void chargerSourcesJuridictions();
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : t("gererCorpus.echecValidationBloc"));
    } finally {
      setValidationBlocEnCours(false);
    }
  };

  return (
    <section className="space-y-4">
      <h2 className="font-serif text-h3 font-semibold text-gold-500">{t("gererCorpus.leCorpus")}</h2>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <Tabs tabs={ONGLETS} actif={onglet} onChange={setOnglet} />
        {onglet === "valide" && (
          <div className="flex flex-wrap gap-2">
            <select className="input w-auto" aria-label={t("gererCorpus.filtrerParSource")} value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="">{t("gererCorpus.toutesLesSources")}</option>
              {SOURCES_CORPUS.filter((s) => s !== "Autre").map((s) => (
                <option key={s} value={s}>
                  {t(`sourceCorpus.${s}`, s)}
                </option>
              ))}
            </select>
            <input className="input w-auto" placeholder={t("gererCorpus.pays")} aria-label={t("gererCorpus.filtrerParPays")} value={pays} onChange={(e) => setPays(e.target.value)} />
            <select className="input w-auto" aria-label={t("gererJurisprudence.filtrerParDomaine")} value={domaine} onChange={(e) => setDomaine(e.target.value)}>
              <option value="">{t("gererJurisprudence.tousLesDomaines")}</option>
              {DOMAINES.map((d) => (
                <option key={d} value={d}>
                  {t(`domaine.${d}`, d)}
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
          titre={onglet === "attente" ? t("gererCorpus.aucunEnAttenteTitre") : t("gererCorpus.aucunValideTitre")}
          description={onglet === "attente" ? t("gererCorpus.aucunEnAttenteDescription") : t("gererCorpus.aucunValideDescription")}
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
                    {source} <span className="font-normal text-warmgray">· {t("gererCorpus.enAttenteCount", { count: totalSource })}</span>
                  </p>
                  {groupesDomaine.length > 1 && totalSource > 1 && (
                    <button
                      onClick={() => setSourceAValiderEnBloc({ source, domaine: "", nombre: totalSource })}
                      className="text-xs text-warmgray underline decoration-dotted hover:text-ivory"
                      title={t("gererCorpus.validerToutTitle")}
                    >
                      {t("gererCorpus.validerToutDunCoup", { count: totalSource })}
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
                          onClick={() => setSourceAValiderEnBloc({ source, domaine: domaine === sansDomainePrecise ? "" : domaine, nombre: items.length })}
                          className="rounded-md border border-risk-low/40 bg-risk-low/10 px-2.5 py-1 text-xs font-semibold text-risk-low transition-colors hover:bg-risk-low/20"
                        >
                          ✓ {t("gererCorpus.validerEnBloc", { count: items.length })}
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
                        t={t}
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
              t={t}
            />
          ))}
        </div>
      )}

      {sourceAValiderEnBloc && (
        <ConfirmerModal
          titre={t("gererCorpus.validerEnBlocTitre")}
          texteBouton={t("gererCorpus.validerEnBlocTitre")}
          enCours={validationBlocEnCours}
          onFermer={() => setSourceAValiderEnBloc(null)}
          onConfirmer={confirmerValidationEnBloc}
          description={
            sourceAValiderEnBloc.domaine ? (
              <p>
                {t("gererCorpus.confirmationDomaineAvant")} <strong className="text-ivory">« {sourceAValiderEnBloc.domaine} »</strong>{" "}
                {t("gererCorpus.confirmationDomaineMilieu", { source: sourceAValiderEnBloc.source, nombre: sourceAValiderEnBloc.nombre })}
              </p>
            ) : (
              <p>
                {t("gererCorpus.confirmationSourceAvant")} <strong className="text-ivory">{t("gererCorpus.touteLaSource", { source: sourceAValiderEnBloc.source })}</strong>{" "}
                {t("gererCorpus.confirmationSourceMilieu", { nombre: sourceAValiderEnBloc.nombre })}
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
  t: TFunction;
}

function LigneCorpus({ item, ouvert, enCours, onToggleLire, onValider, onRejeter, afficherActions, t }: LigneCorpusProps) {
  return (
    <div className="card space-y-2 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ivory">{item.reference || t("gererCorpus.sansReference")}</p>
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
            {ouvert ? t("gererCorpus.masquer") : t("gererCorpus.lire")}
          </button>
          {afficherActions && (
            <>
              <button
                disabled={enCours}
                onClick={onValider}
                className="rounded-md border border-risk-low/40 bg-risk-low/10 px-2.5 py-1 text-xs font-semibold text-risk-low transition-colors hover:bg-risk-low/20 disabled:opacity-40"
              >
                ✓ {t("gererJurisprudence.valider")}
              </button>
              <button
                disabled={enCours}
                onClick={onRejeter}
                className="rounded-md border border-risk-high/40 bg-risk-high/10 px-2.5 py-1 text-xs font-semibold text-risk-high transition-colors hover:bg-risk-high/20 disabled:opacity-40"
              >
                ✕ {t("gererJurisprudence.rejeter")}
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
