/**
 * ConnexionPage — /connexion. Écran d'accès scindé (photo + citation d'un
 * côté, formulaire de l'autre), délibérément sombre -- seule page de toute
 * l'app à déroger au thème clair général (voir globals.css §Page de
 * connexion pour la justification).
 *
 * IMPORTANT — ce formulaire n'est PAS relié à une authentification réelle :
 * il n'existe aujourd'hui aucun système de comptes/session côté backend
 * (Plaid'IA reste un outil à accès libre, protégé uniquement par le mode
 * démo et la clé API personnelle -- voir demo.py). La validation ci-dessous
 * est purement côté client (format des champs) ; la soumission mène vers
 * l'app telle quelle, comme le ferait déjà "Essayer la démo" sur la landing
 * page. Brancher un vrai contrôle d'accès nécessiterait un backend dédié
 * (comptes, mots de passe hashés, codes d'invitation) -- explicitement hors
 * périmètre de cette page, à construire séparément si besoin.
 */

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import Logo from "@/components/Logo";
import Button from "@/components/Button";
import justitiaPhoto from "@/assets/justitia-banniere.jpg";

interface Champs {
  email: string;
  motDePasse: string;
  codeAcces: string;
}

interface Erreurs {
  email?: string;
  motDePasse?: string;
  codeAcces?: string;
}

const RE_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validerChamps(champs: Champs, t: TFunction): Erreurs {
  const erreurs: Erreurs = {};
  if (!champs.email.trim()) {
    erreurs.email = t("connexion.emailRequis");
  } else if (!RE_EMAIL.test(champs.email.trim())) {
    erreurs.email = t("connexion.emailInvalide");
  }
  if (!champs.motDePasse) {
    erreurs.motDePasse = t("connexion.motDePasseRequis");
  } else if (champs.motDePasse.length < 8) {
    erreurs.motDePasse = t("connexion.motDePasseCourt");
  }
  if (!champs.codeAcces.trim()) {
    erreurs.codeAcces = t("connexion.codeAccesRequis");
  }
  return erreurs;
}

export default function ConnexionPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [champs, setChamps] = useState<Champs>({ email: "", motDePasse: "", codeAcces: "" });
  const [erreurs, setErreurs] = useState<Erreurs>({});
  const [envoiEnCours, setEnvoiEnCours] = useState(false);

  const majChamp = (champ: keyof Champs) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setChamps((c) => ({ ...c, [champ]: e.target.value }));
    setErreurs((err) => ({ ...err, [champ]: undefined }));
  };

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    const nouvellesErreurs = validerChamps(champs, t);
    setErreurs(nouvellesErreurs);
    if (Object.keys(nouvellesErreurs).length > 0) return;

    setEnvoiEnCours(true);
    // Pas d'appel réseau réel ici -- voir la note d'en-tête du fichier.
    window.setTimeout(() => {
      navigate("/app/chemise/dossiers");
    }, 500);
  };

  return (
    <div className="connexion-page">
      {/* --- Panneau photo, visible à partir de lg --- */}
      <div className="connexion-photo" aria-hidden="true">
        <img src={justitiaPhoto} alt="" />
        <div className="connexion-photo-scrim" />
        <div className="connexion-photo-wash" />
        <div className="relative z-10 flex h-full flex-col justify-end p-12 xl:p-16">
          <p className="font-mono text-xs uppercase tracking-[0.24em] connexion-accent">{t("connexion.engagementAgentIa")}</p>
          <blockquote className="mt-5 max-w-md font-serif text-3xl font-semibold leading-tight text-white xl:text-4xl">
            {t("connexion.citation")}
          </blockquote>
          <p className="mt-3 text-sm text-white/60">— {t("connexion.citationSource")}</p>
          <p className="mt-8 max-w-sm font-serif text-lg italic leading-snug text-white/85">
            {t("connexion.baseline")}
          </p>
        </div>
      </div>

      {/* --- Même photo, bandeau condensé sous lg --- */}
      <div className="connexion-photo-mobile" aria-hidden="true">
        <img src={justitiaPhoto} alt="" />
        <div className="connexion-photo-scrim" />
        <div className="connexion-photo-wash" />
        <div className="relative z-10 flex h-full flex-col justify-end p-6">
          <p className="font-mono text-[0.65rem] uppercase tracking-[0.2em] connexion-accent">{t("connexion.engagementAgentIa")}</p>
          <p className="mt-1.5 font-serif text-lg font-semibold leading-tight text-white">
            {t("connexion.citationCourte")}
          </p>
        </div>
      </div>

      {/* --- Panneau formulaire --- */}
      <div className="connexion-form-panel">
        <div className="w-full max-w-sm">
          <div className="mb-10 flex items-center gap-2.5">
            <Logo showWordmark={false} iconClassName="h-8 w-8 connexion-accent" />
            <span className="font-display text-2xl font-bold text-white">
              Plaid<span className="connexion-accent">’IA</span>
            </span>
          </div>

          <h1 className="font-serif text-h2 font-semibold text-white">{t("connexion.accederAgentIa")}</h1>
          <p className="mt-2 text-sm text-white/50">{t("connexion.reserveAvocatsGreffiers")}</p>

          <form className="mt-8 space-y-5" onSubmit={soumettre} noValidate>
            <div>
              <label htmlFor="cx-email" className="mb-1.5 block text-sm text-white/70">
                {t("connexion.adresseEmail")}
              </label>
              <input
                id="cx-email"
                type="email"
                autoComplete="email"
                className={`connexion-input ${erreurs.email ? "connexion-input-erreur" : ""}`}
                placeholder="vous@cabinet.fr"
                value={champs.email}
                onChange={majChamp("email")}
                disabled={envoiEnCours}
                aria-invalid={Boolean(erreurs.email)}
                aria-describedby={erreurs.email ? "cx-email-erreur" : undefined}
              />
              {erreurs.email && (
                <p id="cx-email-erreur" className="mt-1.5 text-xs text-risk-high">
                  {erreurs.email}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="cx-mdp" className="mb-1.5 block text-sm text-white/70">
                {t("connexion.motDePasse")}
              </label>
              <input
                id="cx-mdp"
                type="password"
                autoComplete="current-password"
                className={`connexion-input ${erreurs.motDePasse ? "connexion-input-erreur" : ""}`}
                placeholder="••••••••"
                value={champs.motDePasse}
                onChange={majChamp("motDePasse")}
                disabled={envoiEnCours}
                aria-invalid={Boolean(erreurs.motDePasse)}
                aria-describedby={erreurs.motDePasse ? "cx-mdp-erreur" : undefined}
              />
              {erreurs.motDePasse && (
                <p id="cx-mdp-erreur" className="mt-1.5 text-xs text-risk-high">
                  {erreurs.motDePasse}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="cx-code" className="mb-1.5 block text-sm text-white/70">
                {t("connexion.codeAcces")}
              </label>
              <input
                id="cx-code"
                type="text"
                autoComplete="off"
                className={`connexion-input font-mono tracking-wide ${erreurs.codeAcces ? "connexion-input-erreur" : ""}`}
                placeholder={t("connexion.clefInvitation")}
                value={champs.codeAcces}
                onChange={majChamp("codeAcces")}
                disabled={envoiEnCours}
                aria-invalid={Boolean(erreurs.codeAcces)}
                aria-describedby={erreurs.codeAcces ? "cx-code-erreur" : undefined}
              />
              {erreurs.codeAcces && (
                <p id="cx-code-erreur" className="mt-1.5 text-xs text-risk-high">
                  {erreurs.codeAcces}
                </p>
              )}
            </div>

            <Button type="submit" variant="primary" loading={envoiEnCours} className="w-full justify-center">
              {t("connexion.accederAgentIa")}
            </Button>

            <p className="text-center text-xs text-white/40">
              <a href="#" className="hover:text-[#9b59b6]" onClick={(e) => e.preventDefault()}>
                {t("connexion.codeOublie")}
              </a>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
