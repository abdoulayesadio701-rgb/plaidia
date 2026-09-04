/**
 * Button — bouton typé avec état de chargement, sur les classes définies
 * dans globals.css (.btn-primary / .btn-secondary / .btn-ghost).
 */

import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";

const CLASSES: Record<Variant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  icon?: ReactNode;
}

export default function Button({ variant = "primary", loading = false, icon, className = "", children, disabled, ...rest }: ButtonProps) {
  return (
    <button className={`${CLASSES[variant]} ${className}`} disabled={disabled || loading} {...rest}>
      {loading ? (
        <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden="true" />
      ) : (
        icon
      )}
      {children}
    </button>
  );
}
