/**
 * ToastContainer — notifications flottantes (erreurs, confirmations),
 * empilées en bas à droite. Auto-disparition gérée par useAppStore
 * (pousserToast programme le retrait après 6s).
 */

import { useAppStore, type Toast, type ToastType } from "@/store/useAppStore";

// Bordure gauche colorée + icône/texte de la même couleur sur fond surface
// plein (pas de fond translucide) : la lisibilité prime sur l'effet, un
// toast doit se lire d'un coup d'œil quel que soit ce qu'il y a derrière.
const STYLES: Record<ToastType, { accent: string; text: string; icon: string }> = {
  error: { accent: "border-l-risk-high", text: "text-risk-high", icon: "⚠" },
  success: { accent: "border-l-risk-low", text: "text-risk-low", icon: "✓" },
  info: { accent: "border-l-amethyst-400", text: "text-amethyst-400", icon: "ℹ" },
};

function ToastItem({ toast }: { toast: Toast }) {
  const retirerToast = useAppStore((s) => s.retirerToast);
  const styles = STYLES[toast.type];
  return (
    <div
      role="alert"
      className={`flex items-start gap-3 rounded-md border border-gold-600/20 border-l-4 ${styles.accent} bg-surface px-4 py-3 shadow-card animate-[rise_.3s_ease]`}
    >
      <span className={`mt-0.5 shrink-0 ${styles.text}`} aria-hidden="true">
        {styles.icon}
      </span>
      <p className="flex-1 text-sm text-ivory">{toast.message}</p>
      <button
        onClick={() => retirerToast(toast.id)}
        className="shrink-0 text-warmgray hover:text-ivory"
        aria-label="Fermer la notification"
      >
        ✕
      </button>
    </div>
  );
}

export default function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts);
  if (toasts.length === 0) return null;
  return (
    <div className="pointer-events-none fixed bottom-16 right-4 z-50 flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2 sm:bottom-4">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} />
        </div>
      ))}
    </div>
  );
}
