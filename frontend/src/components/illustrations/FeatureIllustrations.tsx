/**
 * FeatureIllustrations — six scènes éditoriales pour la section
 * "Fonctionnalités" de LandingPage.tsx, en remplacement des emojis.
 *
 * Même langage visuel que Logo.tsx : trait fin à épaisseur constante
 * (currentColor, ~1.6px), zéro visage/figure humaine, une seule touche
 * de violet par composition pour désigner l'élément clé de la scène.
 * Volontairement abstraites plutôt que photoréalistes (pas d'outil de
 * génération d'image disponible) mais chacune représente une scène de
 * travail juridique précise et identifiable, jamais une icône générique
 * (pas de balance, pas de marteau, pas de colonnes).
 *
 * Toutes partagent le même viewBox (ratio 8:5) pour un rendu uniforme
 * quel que soit le composant choisi.
 */

interface IllustrationProps {
  className?: string;
}

const VIEWBOX = "0 0 320 200";

/** 1. Analyser des conclusions adverses — feuillet annoté, stylo posé. */
export function IllustrationAnalyser({ className }: IllustrationProps) {
  return (
    <svg viewBox={VIEWBOX} fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {/* Feuillet du dessous, légèrement décalé */}
      <rect x={152} y={22} width={108} height={138} rx={4} opacity={0.35} />
      {/* Feuillet principal */}
      <rect x={112} y={36} width={108} height={138} rx={4} />
      {/* Paragraphe 1 */}
      <path d="M126 56 H196 M126 67 H206 M126 78 H182" opacity={0.7} />
      {/* Ligne annotée -- surlignage court, seule touche de couleur */}
      <path d="M126 96 H198" opacity={0.7} />
      <path d="M126 103.5 H176" className="stroke-amethyst-400" strokeWidth={2.2} />
      {/* Petit repère en marge, à hauteur de l'annotation */}
      <path d="M106 100 Q101 103.5 106 107" opacity={0.6} />
      {/* Paragraphe 3 */}
      <path d="M126 122 H210 M126 133 H190 M126 144 H198" opacity={0.7} />
      {/* Stylo, posé en diagonale sur le coin */}
      <path d="M187 191 L235 152" opacity={0.85} />
      <circle cx={185} cy={193} r={4} opacity={0.85} />
      <path d="M235 152 L242 145 L238 158 Z" className="fill-amethyst-400" stroke="none" />
    </svg>
  );
}

/** 2. Chat juridique — panneau de recherche, pas une bulle de tchat. */
export function IllustrationChat({ className }: IllustrationProps) {
  return (
    <svg viewBox={VIEWBOX} fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {/* Panneau -- écho de .window-bar du hero */}
      <rect x={58} y={28} width={204} height={144} rx={10} />
      <path d="M58 52 H262" opacity={0.5} />
      <circle cx={76} cy={40} r={2.6} opacity={0.6} />
      <circle cx={88} cy={40} r={2.6} opacity={0.6} />
      <circle cx={100} cy={40} r={2.6} opacity={0.6} />
      {/* Barre de recherche */}
      <rect x={74} y={62} width={172} height={18} rx={9} opacity={0.7} />
      <circle cx={88} cy={71} r={4} opacity={0.85} />
      <path d="M91 74 L95 78" opacity={0.85} />
      {/* Résultat en tête -- seule touche de couleur */}
      <rect x={74} y={92} width={38} height={13} rx={3} className="stroke-amethyst-400" strokeWidth={1.8} />
      <path d="M120 98.5 H228" />
      {/* Résultats suivants, plus discrets */}
      <rect x={74} y={116} width={38} height={13} rx={3} opacity={0.4} />
      <path d="M120 122.5 H218 M120 132 H196" opacity={0.55} />
      <rect x={74} y={144} width={38} height={13} rx={3} opacity={0.4} />
      <path d="M120 150.5 H232" opacity={0.55} />
    </svg>
  );
}

/** 3. Plan de plaidoirie chronométré — carnet ouvert, chronomètre discret. */
export function IllustrationPlan({ className }: IllustrationProps) {
  return (
    <svg viewBox={VIEWBOX} fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {/* Carnet ouvert, double page */}
      <rect x={56} y={44} width={192} height={124} rx={6} />
      <path d="M152 44 V168" opacity={0.4} />
      {/* Page gauche -- titre + notes numérotées */}
      <path d="M70 62 H128" opacity={0.85} strokeWidth={2.2} />
      <circle cx={73} cy={80} r={2} opacity={0.7} />
      <path d="M80 80 H136" opacity={0.6} />
      <circle cx={73} cy={94} r={2} opacity={0.7} />
      <path d="M80 94 H140" opacity={0.6} />
      <circle cx={73} cy={108} r={2} opacity={0.7} />
      <path d="M80 108 H124" opacity={0.6} />
      {/* Page droite -- suite + conclusion */}
      <path d="M166 62 H228 M166 74 H216" opacity={0.6} />
      <path d="M166 96 H234" opacity={0.35} />
      <path d="M166 110 H196" opacity={0.85} strokeWidth={2.2} />
      {/* Chronomètre, discret, coin supérieur droit */}
      <circle cx={253} cy={52} r={17} opacity={0.85} />
      <path d="M253 33 V29" opacity={0.85} />
      <path d="M253 39 V42 M253 62 V65 M236 52 H239 M267 52 H270" opacity={0.5} />
      <path d="M253 52 L260 43" className="stroke-amethyst-400" strokeWidth={2} />
    </svg>
  );
}

/** 4. Simulateur d'objections — banc surélevé et pupitre, échange contradictoire. */
export function IllustrationSimulateur({ className }: IllustrationProps) {
  return (
    <svg viewBox={VIEWBOX} fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {/* Banc -- estrade à deux niveaux, nettement surélevée */}
      <path d="M44 120 H124" opacity={0.9} />
      <rect x={48} y={120} width={72} height={30} rx={2} opacity={0.85} />
      <rect x={40} y={150} width={88} height={18} rx={2} opacity={0.85} />
      {/* Pupitre -- pied simple, plan de lecture incliné */}
      <path d="M240 168 V128" opacity={0.85} />
      <path d="M226 168 H254" opacity={0.85} />
      <path d="M218 124 L260 113 L260 120 L218 131 Z" opacity={0.85} />
      <path d="M226 122.5 L246 117.5 M226 126.5 L242 121.5" opacity={0.5} />
      {/* Échange -- chevrons face à face, question / réplique */}
      <path d="M153 90 L170 100 L153 110" opacity={0.75} />
      <path d="M197 108 L180 118 L197 128" className="stroke-amethyst-400" strokeWidth={2} />
    </svg>
  );
}

/** 5. Chronologie automatique — pièces alignées sur une ligne de temps. */
export function IllustrationChronologie({ className }: IllustrationProps) {
  return (
    <svg viewBox={VIEWBOX} fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d="M46 152 H274" opacity={0.6} />
      {/* Pièce 1 */}
      <path d="M62 152 V122" opacity={0.6} />
      <rect x={54} y={98} width={16} height={24} rx={2} opacity={0.6} />
      <circle cx={62} cy={152} r={3.4} opacity={0.8} />
      {/* Pièce 2 */}
      <path d="M110 152 V104" opacity={0.6} />
      <rect x={102} y={76} width={16} height={28} rx={2} opacity={0.6} />
      <circle cx={110} cy={152} r={3.4} opacity={0.8} />
      {/* Pièce 3 -- pièce clé, seule touche de couleur */}
      <path d="M160 152 V84" className="stroke-amethyst-400" />
      <rect x={152} y={56} width={16} height={28} rx={2} className="stroke-amethyst-400" strokeWidth={1.8} />
      <circle cx={160} cy={152} r={4.6} className="fill-amethyst-400" stroke="none" />
      <path d="M160 164 V169" opacity={0.5} />
      {/* Pièce 4 */}
      <path d="M210 152 V114" opacity={0.6} />
      <rect x={202} y={90} width={16} height={24} rx={2} opacity={0.6} />
      <circle cx={210} cy={152} r={3.4} opacity={0.8} />
      {/* Pièce 5 */}
      <path d="M258 152 V120" opacity={0.6} />
      <rect x={250} y={96} width={16} height={24} rx={2} opacity={0.6} />
      <circle cx={258} cy={152} r={3.4} opacity={0.8} />
    </svg>
  );
}

/** 6. Vérification procédurale — checklist et tampon de contrôle. */
export function IllustrationVerification({ className }: IllustrationProps) {
  return (
    <svg viewBox={VIEWBOX} fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <rect x={64} y={32} width={144} height={144} rx={6} />
      {/* Item 1 -- validé */}
      <rect x={80} y={54} width={11} height={11} rx={2.5} className="stroke-amethyst-400" strokeWidth={1.8} />
      <path d="M82.5 59.5 L86 63 L91.5 55.5" className="stroke-amethyst-400" strokeWidth={1.8} />
      <path d="M100 60 H188" opacity={0.7} />
      {/* Item 2 -- validé */}
      <rect x={80} y={80} width={11} height={11} rx={2.5} className="stroke-amethyst-400" strokeWidth={1.8} />
      <path d="M82.5 85.5 L86 89 L91.5 81.5" className="stroke-amethyst-400" strokeWidth={1.8} />
      <path d="M100 86 H192" opacity={0.7} />
      {/* Item 3 -- en attente */}
      <rect x={80} y={106} width={11} height={11} rx={2.5} opacity={0.45} />
      <path d="M100 112 H170" opacity={0.4} />
      {/* Item 4 -- validé */}
      <rect x={80} y={132} width={11} height={11} rx={2.5} className="stroke-amethyst-400" strokeWidth={1.8} />
      <path d="M82.5 137.5 L86 141 L91.5 133.5" className="stroke-amethyst-400" strokeWidth={1.8} />
      <path d="M100 138 H184" opacity={0.7} />
      {/* Tampon de contrôle, coin inférieur droit */}
      <g transform="rotate(-14 236 150)" opacity={0.9}>
        <circle cx={236} cy={150} r={23} className="stroke-amethyst-400" strokeWidth={1.6} />
        <circle cx={236} cy={150} r={15.5} className="stroke-amethyst-400" strokeWidth={1.3} opacity={0.7} />
        <path d="M228 150 L234 156 L245 143" className="stroke-amethyst-400" strokeWidth={1.8} />
      </g>
    </svg>
  );
}
