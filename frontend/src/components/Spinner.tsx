/**
 * Spinner — indicateur de chargement de page, avec le message optionnel
 * affiché sous l'anneau (ex. "Analyse en cours…").
 */

interface SpinnerProps {
  message?: string;
  className?: string;
}

export default function Spinner({ message, className = "" }: SpinnerProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-16 text-center ${className}`}>
      <span
        className="h-8 w-8 animate-spin rounded-full border-2 border-gold-600/30 border-t-gold-500"
        aria-hidden="true"
      />
      {message && <p className="text-sm text-warmgray">{message}</p>}
    </div>
  );
}
