/**
 * GothicMotif — arche gothique ouvragée, filigrane discret.
 *
 * Réservée au bloc d'accueil (voir DESIGN.md §4 "Motif d'arrière-plan") —
 * ne jamais l'utiliser en pattern répété sur les écrans de travail
 * (dossiers, analyses), où elle distrairait de la lecture.
 *
 * Trois arcs emboîtés (portail, tympan, ébrasement) + meneau central +
 * rosace à quatrefeuille encadrée, inspirés des arches du mood-board de
 * référence — plus riche que l'arc simple d'origine, en restant un tracé
 * fin exploitable à très faible opacité (4-6 %).
 *
 * Usage :
 *   <div className="relative overflow-hidden">
 *     <GothicMotif className="absolute inset-0 h-full w-auto opacity-[0.05]" />
 *     ...contenu du hero...
 *   </div>
 */

interface GothicMotifProps {
  className?: string;
}

export default function GothicMotif({ className }: GothicMotifProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 400 600"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      aria-hidden="true"
    >
      {/* Portail — arche brisée à deux centres, la plus classique du gothique rayonnant */}
      <path d="M60 560 V400 A240 240 0 0 1 180 192 A240 240 0 0 1 300 400 V560" />
      {/* Tympan — second arc, suggère l'épaisseur de la voussure */}
      <path d="M84 560 V404 A200 200 0 0 1 182 214 A200 200 0 0 1 276 404 V560" opacity={0.6} />
      {/* Ébrasement intérieur — troisième arc, profondeur du portail */}
      <path d="M106 560 V408 A170 170 0 0 1 180 245 A170 170 0 0 1 254 408 V560" opacity={0.4} />
      {/* Meneau central */}
      <path d="M180 560 V245" opacity={0.5} />
      {/* Rosace encadrée à quatrefeuille */}
      <circle cx={180} cy={165} r={24} opacity={0.8} />
      <circle cx={180} cy={165} r={13} />
      <circle cx={180} cy={150} r={7} />
      <circle cx={180} cy={180} r={7} />
      <circle cx={165} cy={165} r={7} />
      <circle cx={195} cy={165} r={7} />
      {/* Cabochon améthyste au cœur de la rosace — écho du pivot de Logo.tsx */}
      <circle cx={180} cy={165} r={3} className="fill-amethyst-400" stroke="none" />
    </svg>
  );
}
