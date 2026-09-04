import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-md py-20 text-center">
      <p className="font-display text-5xl font-bold text-gold-500">404</p>
      <p className="mt-3 text-sm text-warmgray">Cette page n'existe pas.</p>
      <Link to="/" className="btn-secondary mt-6 inline-flex">
        Retour à l'accueil
      </Link>
    </div>
  );
}
