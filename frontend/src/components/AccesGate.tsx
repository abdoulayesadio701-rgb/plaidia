/**
 * AccesGate : barrière de mot de passe devant toute l'app (/app/*), active
 * seulement si le serveur en exige un (GET /api/config -> acces_protege,
 * voir backend/app/acces.py). Sans mot de passe configuré côté serveur,
 * n'affiche rien de plus : les enfants sont rendus tout de suite.
 *
 * Si le serveur est injoignable ou répond autre chose qu'un 401, on laisse
 * passer : l'app affiche déjà ses propres erreurs de connexion, mieux vaut
 * ne pas enfermer l'utilisateur derrière un formulaire qui ne peut rien
 * vérifier.
 */

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/api/http";
import { obtenirConfiguration, verifierAcces } from "@/api/config";
import { definirMotDePasseAcces } from "@/api/accesMotDePasse";
import Button from "@/components/Button";
import Logo from "@/components/Logo";

type Etat = "verification" | "libre" | "demande";

export default function AccesGate({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const [etat, setEtat] = useState<Etat>("verification");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState(false);
  const [envoi, setEnvoi] = useState(false);

  useEffect(() => {
    let actif = true;
    (async () => {
      try {
        const config = await obtenirConfiguration();
        if (!config.acces_protege) {
          if (actif) setEtat("libre");
          return;
        }
        await verifierAcces();
        if (actif) setEtat("libre");
      } catch (e) {
        if (!actif) return;
        setEtat(e instanceof ApiError && e.status === 401 ? "demande" : "libre");
      }
    })();
    return () => {
      actif = false;
    };
  }, []);

  const valider = async (e: FormEvent) => {
    e.preventDefault();
    if (!motDePasse.trim()) return;
    setEnvoi(true);
    setErreur(false);
    definirMotDePasseAcces(motDePasse);
    try {
      await verifierAcces();
      setEtat("libre");
    } catch (err) {
      definirMotDePasseAcces(null);
      if (err instanceof ApiError && err.status === 401) setErreur(true);
      else setEtat("libre");
    } finally {
      setEnvoi(false);
    }
  };

  if (etat === "libre") return <>{children}</>;

  if (etat === "verification") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-void text-warmgray" role="status">
        {t("acces.verification")}
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-void px-6 text-ivory">
      <form onSubmit={valider} className="card w-full max-w-sm space-y-4 p-6">
        <Logo />
        <h1 className="font-serif text-h3 font-semibold text-gold-500">{t("acces.titre")}</h1>
        <p className="text-sm text-warmgray">{t("acces.description")}</p>
        <label className="block text-sm">
          <span className="sr-only">{t("acces.motDePasse")}</span>
          <input
            type="password"
            className="input"
            placeholder={t("acces.motDePasse")}
            value={motDePasse}
            onChange={(ev) => setMotDePasse(ev.target.value)}
            autoFocus
            autoComplete="current-password"
          />
        </label>
        {erreur && (
          <p role="alert" className="text-sm text-risk-high">
            {t("acces.incorrect")}
          </p>
        )}
        <Button type="submit" loading={envoi} disabled={!motDePasse.trim()} className="w-full">
          {t("acces.valider")}
        </Button>
      </form>
    </div>
  );
}
