/**
 * PagePlaceholder — contenu provisoire d'une page pas encore implémentée.
 * Utilisé par toutes les routes déclarées dans navigation.ts en attendant
 * leur page réelle (voir router.tsx) — retirer au fur et à mesure qu'une
 * page reçoit son vrai composant.
 */

interface PagePlaceholderProps {
  title: string;
  description?: string;
}

export default function PagePlaceholder({ title, description }: PagePlaceholderProps) {
  return (
    <div className="card mx-auto max-w-2xl p-8 text-center">
      <p className="kicker">Bientôt disponible</p>
      <h1 className="mt-3 font-serif text-h2 font-semibold text-gold-500">{title}</h1>
      {description && <p className="mt-3 text-sm text-warmgray">{description}</p>}
      <p className="mt-6 text-xs text-muted">Cette page sera implémentée dans une prochaine étape.</p>
    </div>
  );
}
