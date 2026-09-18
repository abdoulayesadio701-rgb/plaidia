/** BlocListe — carte « titre + liste à puces » des résultats d'analyse
 * structurés (réquisitoire, rapport d'instruction). Une liste vide affiche
 * « rien détecté » plutôt que de disparaître : l'absence est une information. */

import { useTranslation } from "react-i18next";

interface BlocListeProps {
  titre: string;
  elements: string[];
  icone?: string;
}

export default function BlocListe({ titre, elements, icone }: BlocListeProps) {
  const { t } = useTranslation();
  return (
    <div className="card space-y-2.5 p-5">
      <p className="font-serif text-h4 font-semibold text-ivory">
        {icone ? `${icone} ` : ""}
        {titre}
      </p>
      {elements.length === 0 ? (
        <p className="text-sm text-muted">{t("extraction.rienDetecte")}</p>
      ) : (
        <ul className="space-y-1.5 text-sm text-ivory">
          {elements.map((element, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-gold-500">•</span>
              {element}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
