/**
 * RichOutput — rend le texte produit par l'agent : titres, listes, **gras**,
 * et surligne chaque occurrence de "À VÉRIFIER" (le garde-fou
 * anti-hallucination, voir DESIGN.md §1.6). Reproduit l'esprit de
 * PlaidIAApp._afficher() dans gui.py, étendu au markdown léger que
 * produisent les prompts (QUESTION_SYSTEM_PROMPT demande explicitement
 * des listes à puces et du **gras**).
 *
 * Pensé pour le streaming : ce composant reçoit à chaque frappe le texte
 * COMPLET accumulé jusque-là (pas un fragment isolé) et reparse tout à
 * chaque rendu. C'est ce qui rend le surlignage de "À VÉRIFIER" robuste
 * même si le marqueur est coupé entre deux fragments SSE — contrairement
 * à gui.py qui devait bufferiser manuellement avant d'insérer dans un
 * widget Tkinter, React re-render simplement la chaîne à jour : tant que
 * le marqueur n'est pas entièrement arrivé, il s'affiche en texte brut ;
 * dès qu'il l'est, le rendu suivant le repère et l'habille — aucune
 * bufferisation à gérer côté composant.
 */

import type { ReactNode } from "react";

const MARQUEUR = "À VÉRIFIER";
// Alterne entre "**gras**" et le marqueur en un seul passage, pour ne
// jamais laisser un "**" avaler accidentellement le marqueur voisin.
const SEGMENT_RE = /(\*\*[^*]+\*\*|À VÉRIFIER)/g;

function renderInline(segment: string, keyPrefix: string): ReactNode[] {
  const parts = segment.split(SEGMENT_RE).filter((p) => p !== "");
  return parts.map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (part === MARQUEUR) {
      return (
        <mark key={key} className="marker-verify">
          {MARQUEUR}
        </mark>
      );
    }
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={key}>{part.slice(2, -2)}</strong>;
    }
    return <span key={key}>{part}</span>;
  });
}

type Bloc =
  | { type: "titre"; niveau: 1 | 2 | 3; texte: string }
  | { type: "liste"; ordonnee: boolean; items: string[] }
  | { type: "paragraphe"; lignes: string[] };

const RE_TITRE = /^(#{1,3})\s+(.*)$/;
const RE_PUCE = /^[-*]\s+(.*)$/;
const RE_NUMEROTEE = /^\d+[.)]\s+(.*)$/;

/** Regroupe les lignes en blocs (titre / liste / paragraphe) — parseur
 * volontairement minimal : c'est tout ce que produisent les prompts
 * (voir analyse.py), pas un moteur markdown généraliste. */
function parseBlocs(texte: string): Bloc[] {
  const lignes = texte.split("\n");
  const blocs: Bloc[] = [];
  let paragrapheCourant: string[] = [];
  let listeCourante: { ordonnee: boolean; items: string[] } | null = null;

  const clorepParagraphe = () => {
    if (paragrapheCourant.length) {
      blocs.push({ type: "paragraphe", lignes: paragrapheCourant });
      paragrapheCourant = [];
    }
  };
  const clorepListe = () => {
    if (listeCourante) {
      blocs.push({ type: "liste", ordonnee: listeCourante.ordonnee, items: listeCourante.items });
      listeCourante = null;
    }
  };

  for (const ligneBrute of lignes) {
    const ligne = ligneBrute.trimEnd();

    if (ligne.trim() === "") {
      clorepParagraphe();
      clorepListe();
      continue;
    }

    const matchTitre = ligne.match(RE_TITRE);
    if (matchTitre) {
      clorepParagraphe();
      clorepListe();
      blocs.push({ type: "titre", niveau: matchTitre[1].length as 1 | 2 | 3, texte: matchTitre[2] });
      continue;
    }

    const matchPuce = ligne.match(RE_PUCE);
    const matchNumerotee = !matchPuce ? ligne.match(RE_NUMEROTEE) : null;
    if (matchPuce || matchNumerotee) {
      clorepParagraphe();
      const ordonnee = Boolean(matchNumerotee);
      const contenu = (matchPuce ?? matchNumerotee)![1];
      if (!listeCourante || listeCourante.ordonnee !== ordonnee) {
        clorepListe();
        listeCourante = { ordonnee, items: [] };
      }
      listeCourante.items.push(contenu);
      continue;
    }

    clorepListe();
    paragrapheCourant.push(ligne);
  }
  clorepParagraphe();
  clorepListe();
  return blocs;
}

const TAILLES_TITRE: Record<1 | 2 | 3, string> = {
  1: "mt-5 font-serif text-h3 font-semibold text-gold-500",
  2: "mt-4 font-serif text-h4 font-semibold text-gold-500",
  3: "mt-3 text-sm font-semibold uppercase tracking-wide text-amethyst-400",
};

interface RichOutputProps {
  texte: string;
  className?: string;
  /** Contrainte de largeur de lecture (voir DESIGN.md §2, ~65ch) — activée par défaut. */
  prose?: boolean;
}

export default function RichOutput({ texte, className = "", prose = true }: RichOutputProps) {
  const blocs = parseBlocs(texte);
  return (
    <div className={`${prose ? "max-w-prose" : ""} space-y-3 text-ivory ${className}`}>
      {blocs.map((bloc, i) => {
        if (bloc.type === "titre") {
          const Balise = `h${bloc.niveau}` as keyof JSX.IntrinsicElements;
          return (
            <Balise key={i} className={TAILLES_TITRE[bloc.niveau]}>
              {renderInline(bloc.texte, `t${i}`)}
            </Balise>
          );
        }
        if (bloc.type === "liste") {
          const ListeBalise = bloc.ordonnee ? "ol" : "ul";
          return (
            <ListeBalise key={i} className={`ml-5 space-y-1 text-body leading-relaxed ${bloc.ordonnee ? "list-decimal" : "list-disc"}`}>
              {bloc.items.map((item, j) => (
                <li key={j}>{renderInline(item, `l${i}-${j}`)}</li>
              ))}
            </ListeBalise>
          );
        }
        return (
          <p key={i} className="text-body leading-relaxed">
            {bloc.lignes.map((ligne, j) => (
              <span key={j}>
                {renderInline(ligne, `p${i}-${j}`)}
                {j < bloc.lignes.length - 1 && <br />}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
