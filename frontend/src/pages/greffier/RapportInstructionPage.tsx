/**
 * RapportInstructionPage — /greffier/rapport-instruction. Analyse d'un
 * rapport d'instruction : actes accomplis, éléments à charge et à décharge,
 * mesures ordonnées, sens proposé, points d'attention. Voir PageAnalyseTexte
 * pour le squelette commun (collage/import, export Word, persistance locale).
 */

import { useTranslation } from "react-i18next";
import { greffier as greffierApi } from "@/api";
import BlocListe from "@/components/BlocListe";
import PageAnalyseTexte from "@/components/PageAnalyseTexte";

export default function RapportInstructionPage() {
  const { t } = useTranslation();
  return (
    <PageAnalyseTexte
      cle="rapport-instruction"
      titre={t("nav.greffier.rapport-instruction")}
      sousTitre={t("rapportInstruction.sousTitre")}
      placeholder={t("rapportInstruction.placeholder")}
      libelleLancer={t("rapportInstruction.analyser")}
      pretTitre={t("rapportInstruction.pretTitre")}
      pretDescription={t("rapportInstruction.pretDescription")}
      nomFichierExport="rapport_instruction.docx"
      lancer={greffierApi.analyserRapportInstruction}
      exporter={greffierApi.exporterRapportInstruction}
      rendreResultat={(r) => (
        <>
          <div className="card space-y-1 p-5">
            <p className="text-micro font-medium uppercase tracking-wide text-amethyst-400">{t("rapportInstruction.sensPropose")}</p>
            <p className="text-sm font-medium text-gold-500">{r.sens_propose}</p>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <BlocListe icone="🗂" titre={t("rapportInstruction.actes")} elements={r.actes_instruction} />
            <BlocListe icone="📥" titre={t("rapportInstruction.mesures")} elements={r.mesures_ordonnees} />
            <BlocListe icone="⚖" titre={t("rapportInstruction.aCharge")} elements={r.elements_a_charge} />
            <BlocListe icone="🛡" titre={t("rapportInstruction.aDecharge")} elements={r.elements_a_decharge} />
          </div>
          <BlocListe icone="🔎" titre={t("rapportInstruction.pointsAttention")} elements={r.points_attention} />
        </>
      )}
    />
  );
}
