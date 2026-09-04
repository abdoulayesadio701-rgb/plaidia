/**
 * Logo — glyphe balance abstrait + mot-marque "Plaid'IA".
 * Voir DESIGN.md §5 : icône toujours à gauche, trait d'épaisseur
 * constante, apostrophe typographique (’) dans le mot-marque.
 *
 * Deuxième itération, après retour utilisateur sur la première version
 * (balance ouvragée à fronton/volutes/socle à degrés) : trop illustrative,
 * elle lisait comme du clip-art plutôt que comme une marque. Un glyphe
 * abstrait à 7 primitives — un fléau à peine courbé, deux fils, deux
 * plateaux réduits à un point, un fût, une base — porte mieux la marque
 * à toutes les échelles (barre latérale, favicon) et se rapproche des
 * marques 2025+ que du blason gravé. Le cabochon améthyste au pivot
 * reste l'unique touche de couleur — c'est le seul détail conservé de
 * la première itération.
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
  wordmarkClassName = "font-display text-2xl font-bold text-gold-500",
  showWordmark = true,
}: LogoProps) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" className={iconClassName}>
        {/* Fléau — légèrement arqué plutôt que rigide */}
        <path d="M8 14 Q20 11 32 14" />
        {/* Fût et base */}
        <path d="M20 14 V30" />
        <path d="M14 30 H26" />
        {/* Plateaux — réduits à un fil et un point, pas une coupelle illustrée */}
        <path d="M8 14 V22" />
        <circle cx={8} cy={24.5} r={2} />
        <path d="M32 14 V22" />
        <circle cx={32} cy={24.5} r={2} />
        {/* Pivot — cabochon améthyste, seule touche de couleur */}
        <circle cx={20} cy={14} r={2} className="fill-amethyst-400" stroke="none" />
      </svg>
      {showWordmark && <span className={wordmarkClassName}>Plaid’IA</span>}
    </div>
  );
}
