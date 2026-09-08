/**
 * CoherencePage — /greffier/coherence. Ajout de 2 documents ou plus
 * (nom + texte, saisie collée -- POST /api/greffier/coherence exige
 * min_length=2 côté backend), tableau des contradictions trié par gravité
 * décroissante, éléments cohérents, limites de l'analyse.
 */

import { useState } from "react";
import { dossiers as dossiersApi, greffier as greffierApi } from "@/api";
import type { Contradiction } from "@/api";
import { useAppStore } from "@/store/useAppStore";
import { useLazyAction } from "@/hooks/useLazyAction";
import { EXTENSIONS_DOCUMENT } from "@/config/fichiers";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import FileDropZone from "@/components/FileDropZone";
import RichOutput from "@/components/RichOutput";
import { SkeletonList } from "@/components/Skeleton";
import ChatContextuelPanel from "@/components/chat/ChatContextuelPanel";

interface DocumentBrouillon {
  id: string;
  nomDocument: string;
  texte: string;
}

const CLASSE_GRAVITE: Record<string, string> = {
  Élevée: "badge-risk-high",
  Moyenne: "badge-risk-medium",
  Faible: "badge-risk-low",
};
const ORDRE_GRAVITE: Record<string, number> = { Élevée: 0, Moyenne: 1, Faible: 2 };

function nouveauDocument(numero: number): DocumentBrouillon {
  return { id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, nomDocument: `Document ${numero}`, texte: "" };
}

export default function CoherencePage() {
  const pousserToast = useAppStore((s) => s.pousserToast);
  const [documents, setDocuments] = useState<DocumentBrouillon[]>([nouveauDocument(1), nouveauDocument(2)]);
  const [idEnImport, setIdEnImport] = useState<string | null>(null);

  const { data, loading, error, executer, definirDonnees } = useLazyAction((docs: { nom_document: string; texte: string }[]) =>
    greffierApi.controleCoherence(docs)
  );

  const majDocument = (id: string, patch: Partial<DocumentBrouillon>) =>
    setDocuments((liste) => liste.map((d) => (d.id === id ? { ...d, ...patch } : d)));

  const importerFichier = async (id: string, fichier: File) => {
    setIdEnImport(id);
    try {
      const resultat = await dossiersApi.extraireFichier(fichier);
      majDocument(id, { texte: resultat.texte_extrait });
      pousserToast("success", `« ${resultat.nom_fichier} » importé (${resultat.caracteres_extraits.toLocaleString("fr-FR")} caractères).`);
    } catch (e) {
      pousserToast("error", e instanceof Error ? e.message : "Échec de l'import du fichier.");
    } finally {
      setIdEnImport(null);
    }
  };

  const ajouterDocument = () => setDocuments((liste) => [...liste, nouveauDocument(liste.length + 1)]);

  const retirerDocument = (id: string) => setDocuments((liste) => liste.filter((d) => d.id !== id));

  const documentsValides = documents.filter((d) => d.nomDocument.trim() && d.texte.trim());
  const peutLancer = documentsValides.length >= 2;

  const lancer = () =>
    void executer(documentsValides.map((d) => ({ nom_document: d.nomDocument.trim(), texte: d.texte.trim() })));

  const contradictionsTriees = data
    ? [...data.contradictions].sort((a, b) => (ORDRE_GRAVITE[a.gravite] ?? 3) - (ORDRE_GRAVITE[b.gravite] ?? 3))
    : [];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <p className="kicker">Le Greffier</p>
        <h1 className="mt-1 font-serif text-h2 font-semibold text-gold-500">Contrôle de cohérence entre documents</h1>
        <p className="mt-2 text-sm text-warmgray">Compare au moins deux documents pour repérer les contradictions factuelles (dates, montants, noms…).</p>
      </div>

      <div className="space-y-4">
        {documents.map((doc, i) => (
          <div key={doc.id} className="card space-y-3 p-5">
            <div className="flex items-center justify-between gap-3">
              <input
                className="input max-w-xs font-medium"
                value={doc.nomDocument}
                onChange={(e) => majDocument(doc.id, { nomDocument: e.target.value })}
                placeholder={`Document ${i + 1}`}
                disabled={loading}
              />
              {documents.length > 2 && (
                <button onClick={() => retirerDocument(doc.id)} className="text-xs text-muted hover:text-risk-high" disabled={loading}>
                  ✕ Retirer
                </button>
              )}
            </div>
            <textarea
              className="input min-h-[140px] resize-y"
              placeholder="Collez ici le texte de ce document…"
              value={doc.texte}
              onChange={(e) => majDocument(doc.id, { texte: e.target.value })}
              disabled={loading || idEnImport === doc.id}
            />
            <FileDropZone
              variante="compact"
              extensions={EXTENSIONS_DOCUMENT}
              loading={idEnImport === doc.id}
              disabled={loading || (idEnImport !== null && idEnImport !== doc.id)}
              className="text-xs"
              onFichiers={(fichiers) => void importerFichier(doc.id, fichiers[0])}
            />
          </div>
        ))}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <button onClick={ajouterDocument} disabled={loading} className="text-sm text-amethyst-400 hover:underline">
            ＋ Ajouter un document
          </button>
          <Button variant="primary" loading={loading} disabled={!peutLancer} onClick={lancer}>
            Contrôler la cohérence
          </Button>
        </div>
        {!peutLancer && <p className="text-xs text-muted">Au moins deux documents avec un nom et un texte sont nécessaires.</p>}
      </div>

      {loading && <SkeletonList count={2} />}

      {!loading && error && <ErrorState message={error} onRetry={lancer} />}

      {!loading && !error && data && (
        <div className="space-y-6">
          <div>
            <p className="mb-3 font-serif text-h3 font-semibold text-gold-500">Contradictions</p>
            {contradictionsTriees.length === 0 ? (
              <EmptyState titre="Aucune contradiction détectée" description="Les documents fournis ne présentent pas d'incohérence factuelle apparente." />
            ) : (
              <div className="overflow-x-auto rounded-md border border-gold-600/20">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-gold-600/20 bg-surface-2 text-left text-micro uppercase tracking-wide text-warmgray">
                      <th className="px-4 py-3 font-medium">Gravité</th>
                      <th className="px-4 py-3 font-medium">Sujet</th>
                      <th className="px-4 py-3 font-medium">Document 1</th>
                      <th className="px-4 py-3 font-medium">Document 2</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contradictionsTriees.map((c: Contradiction, i) => (
                      <tr key={i} className="border-b border-gold-600/10 last:border-0 hover:bg-surface-2/40">
                        <td className="px-4 py-3">
                          <span className={CLASSE_GRAVITE[c.gravite] ?? "badge border-muted/30 bg-surface-2 text-warmgray"}>{c.gravite}</span>
                        </td>
                        <td className="px-4 py-3 font-medium text-ivory">{c.sujet}</td>
                        <td className="max-w-xs px-4 py-3 text-warmgray">{c.document_1}</td>
                        <td className="max-w-xs px-4 py-3 text-warmgray">{c.document_2}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {data.elements_coherents.length > 0 && (
            <div className="rounded-md border border-risk-low/30 bg-risk-low/10 p-5">
              <p className="mb-2 text-sm font-semibold text-risk-low">✓ Éléments cohérents</p>
              <ul className="space-y-1.5">
                {data.elements_coherents.map((el, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ivory">
                    <span className="text-risk-low">•</span>
                    {el}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.limites_analyse && (
            <div className="card p-5">
              <p className="mb-2 text-micro font-medium uppercase tracking-wide text-warmgray">Limites de l'analyse</p>
              <RichOutput texte={data.limites_analyse} prose={false} className="text-sm" />
            </div>
          )}

          <ChatContextuelPanel
            feature="coherence"
            resultatActuel={data}
            onMiseAJour={definirDonnees}
            placeholder="Ex. « Explique cette contradiction plus en détail », « compare ces deux documents »…"
          />
        </div>
      )}
    </div>
  );
}
