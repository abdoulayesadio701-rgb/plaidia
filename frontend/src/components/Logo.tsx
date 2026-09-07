/**
 * Logo — balance de la justice (glyphe raffiné) + mot-marque "Plaid'IA".
 * Voir DESIGN.md §5 : icône toujours à gauche, apostrophe typographique
 * (’) dans le mot-marque.
 *
 * Troisième itération. La première (balance ouvragée à fronton/volutes/
 * socle à degrés) lisait comme du clip-art. La deuxième, 7 primitives
 * abstraites, était juste mais un peu froide -- reconnaissable comme
 * "une balance" sans évoquer LA balance de la justice, l'symbole que
 * tout juriste identifie au premier coup d'oeil (fronton de tribunal,
 * robe, sceaux). Celle-ci reprend l'anneau de suspension (on la
 * brandit, elle ne repose pas sur un socle) et des plateaux en coupelle
 * plutôt qu'un point -- silhouette immédiatement lisible comme "scales
 * of justice", en gardant un tracé fin à épaisseur constante, sans
 * remplissage illustratif. Le cabochon violet au pivot reste l'unique
 * touche de couleur du glyphe.
 *
 * Mot-marque : "Plaid" (la plaidoirie) en encre, "’IA" en accent violet
 * -- sépare visuellement les deux racines du nom sans ajouter d'élément.
 */

interface LogoProps {
  className?: string;
  iconClassName?: string;
  wordmarkClassName?: string;
  showWordmark?: boolean;
}

export default function Logo({
  className = "",
  iconClassName = "h-7 w-7 text-gold-500",
  wordmarkClassName = "font-display text-2xl font-bold",
  showWordmark = true,
}: LogoProps) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={iconClassName}>
        {/* Anneau de suspension -- on la brandit, elle ne repose pas sur un socle */}
        <circle cx={20} cy={5.6} r={2.1} />
        <path d="M20 7.7 V11.8" />
        {/* Fléau -- arche gracieuse */}
        <path d="M7 15 Q20 11 33 15" />
        {/* Fût et base */}
        <path d="M20 15 V31" />
        <path d="M13 31 H27" />
        {/* Plateau gauche -- suspendu par deux fils, coupelle en arc */}
        <path d="M7 15 L4.5 22.5 M7 15 L9.5 22.5" />
        <path d="M3 22.5 Q7 26.5 11 22.5" />
        {/* Plateau droit -- symétrique */}
        <path d="M33 15 L30.5 22.5 M33 15 L35.5 22.5" />
        <path d="M29 22.5 Q33 26.5 37 22.5" />
        {/* Pivot -- cabochon violet, seule touche de couleur */}
        <circle cx={20} cy={15} r={1.9} className="fill-amethyst-400" stroke="none" />
      </svg>
      {showWordmark && (
        <span className={wordmarkClassName}>
          <span className="text-amethyst-600">Plaid</span>
          <span className="text-amethyst-400">’IA</span>
        </span>
      )}
    </div>
  );
}
