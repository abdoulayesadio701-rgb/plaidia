import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-md py-20 text-center">
      <p className="font-display text-5xl font-bold text-gold-500">404</p>
      <p className="mt-3 text-sm text-warmgray">{t("notFound.pageInexistante")}</p>
      <Link to="/" className="btn-secondary mt-6 inline-flex">
        {t("notFound.retourAccueil")}
      </Link>
    </div>
  );
}
