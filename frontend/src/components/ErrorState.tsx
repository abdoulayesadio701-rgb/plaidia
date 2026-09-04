/**
 * ErrorState — état d'erreur de page (à distinguer des toasts : ceci
 * remplace le contenu de la zone de résultat, pour une erreur qui empêche
 * la page de faire son travail — un simple avertissement passe par un toast).
 */

import Button from "./Button";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-md border border-risk-high/30 bg-risk-high/10 px-6 py-10 text-center">
      <p className="text-2xl" aria-hidden="true">
        ⚠
      </p>
      <p className="max-w-md text-sm text-ivory">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Réessayer
        </Button>
      )}
    </div>
  );
}
