/**
 * RequisitoirePage — /greffier/requisitoire. Analyse d'un réquisitoire :
 * qualification retenue, faits invoqués, circonstances aggravantes et
 * atténuantes, peine requise, points d'attention. Voir PageAnalyseTexte pour
 * le squelette commun (collage/import, export Word, persistance locale).
 */

import { useTranslation } from "react-i18next";
import { greffier as greffierApi } from "@/api";
import BlocListe from "@/components/BlocListe";
import PageAnalyseTexte from "@/components/PageAnalyseTexte";

export default function RequisitoirePage() {
  const { t } = useTranslation();
  return (
    <PageAnalyseTexte
      cle="requisitoire"
      titre={t("nav.greffier.requisitoire")}
      sousTitre={t("requisitoire.sousTitre")}
      placeholder={t("requisitoire.placeholder")}
      libelleLancer={t("requisitoire.analyser")}
      pretTitre={t("requisitoire.pretTitre")}
      pretDescription={t("requisitoire.pretDescription")}
      nomFichierExport="requisitoire.docx"
      lancer={greffierApi.analyserRequisitoire}
      exporter={greffierApi.exporterRequisitoire}
      rendreResultat={(r) => (
        <>
          <div className="card space-y-3 p-5">
            <div>
              <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{t("requisitoire.qualification")}</p>
              <p className="mt-1 text-sm text-ivory">{r.qualification_retenue || t("requisitoire.nonPrecisee")}</p>
            </div>
            <div>
              <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{t("requisitoire.peineRequise")}</p>
              <p className="mt-1 text-sm font-medium text-gold-500">{r.peine_requise}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <BlocListe icone="📌" titre={t("requisitoire.faits")} elements={r.faits_et_elements_invoques} />
            <BlocListe icone="⚠" titre={t("requisitoire.aggravantes")} elements={r.circonstances_aggravantes} />
            <BlocListe icone="🕊" titre={t("requisitoire.attenuantes")} elements={r.circonstances_attenuantes} />
            <BlocListe icone="🔎" titre={t("requisitoire.pointsAttention")} elements={r.points_attention} />
          </div>
        </>
      )}
    />
  );
}
