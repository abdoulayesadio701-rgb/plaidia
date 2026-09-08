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

function validerChamps(champs: Champs): Erreurs {
  const erreurs: Erreurs = {};
  if (!champs.email.trim()) {
    erreurs.email = "L'adresse e-mail est requise.";
  } else if (!RE_EMAIL.test(champs.email.trim())) {
    erreurs.email = "Adresse e-mail invalide.";
  }
  if (!champs.motDePasse) {
    erreurs.motDePasse = "Le mot de passe est requis.";
  } else if (champs.motDePasse.length < 8) {
    erreurs.motDePasse = "8 caractères minimum.";
  }
  if (!champs.codeAcces.trim()) {
    erreurs.codeAcces = "Le code d'accès est requis.";
  }
  return erreurs;
}

export default function ConnexionPage() {
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
    const nouvellesErreurs = validerChamps(champs);
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
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-amethyst-400">L'engagement de l'agent IA</p>
          <blockquote className="mt-5 max-w-md font-serif text-3xl font-semibold leading-tight text-white xl:text-4xl">
            « Les hommes naissent et demeurent libres et égaux en droits. »
          </blockquote>
          <p className="mt-3 text-sm text-white/60">— Déclaration des droits de l'homme et du citoyen (1789)</p>
          <p className="mt-8 max-w-sm font-serif text-lg italic leading-snug text-white/85">
            Une justice éclairée et accessible à chacun, à chaque instant.
          </p>
        </div>
      </div>

      {/* --- Même photo, bandeau condensé sous lg --- */}
      <div className="connexion-photo-mobile" aria-hidden="true">
        <img src={justitiaPhoto} alt="" />
        <div className="connexion-photo-scrim" />
        <div className="connexion-photo-wash" />
        <div className="relative z-10 flex h-full flex-col justify-end p-6">
          <p className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-amethyst-400">L'engagement de l'agent IA</p>
          <p className="mt-1.5 font-serif text-lg font-semibold leading-tight text-white">
            « Libres et égaux en droits. »
          </p>
        </div>
      </div>

      {/* --- Panneau formulaire --- */}
      <div className="connexion-form-panel">
        <div className="w-full max-w-sm">
          <div className="mb-10 flex items-center gap-2.5">
            <Logo showWordmark={false} iconClassName="h-8 w-8 text-amethyst-400" />
            <span className="font-display text-2xl font-bold text-white">
              Plaid<span className="text-amethyst-400">’IA</span>
            </span>
          </div>

          <h1 className="font-serif text-h2 font-semibold text-white">Accéder à l'agent IA</h1>
          <p className="mt-2 text-sm text-white/50">Réservé aux avocats et greffiers invités.</p>

          <form className="mt-8 space-y-5" onSubmit={soumettre} noValidate>
            <div>
              <label htmlFor="cx-email" className="mb-1.5 block text-sm text-white/70">
                Adresse e-mail
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
                Mot de passe
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
                Code d'accès
              </label>
              <input
                id="cx-code"
                type="text"
                autoComplete="off"
                className={`connexion-input font-mono tracking-wide ${erreurs.codeAcces ? "connexion-input-erreur" : ""}`}
                placeholder="Clef d'invitation"
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
              Accéder à l'agent IA
            </Button>

            <p className="text-center text-xs text-white/40">
              <a href="#" className="hover:text-amethyst-400" onClick={(e) => e.preventDefault()}>
                Code oublié ? Demander un accès
              </a>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
