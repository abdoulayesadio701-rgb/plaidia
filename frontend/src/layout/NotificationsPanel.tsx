/**
 * NotificationsPanel — liste déroulante des notifications de veille
 * (jurisprudence + articles de loi modifiés + rappel OHADA) -- portage web
 * de gui.py::DialogueNotificationsVeille. Voir useAppStore::notificationsVeille,
 * rafraîchi périodiquement par AppLayout et par la boucle serveur horaire
 * (backend/app/veille.py).
 */

import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { veille as veilleApi } from "@/api";
import { useAppStore } from "@/store/useAppStore";

interface NotificationsPanelProps {
  onFermer: () => void;
}

const CODES_LIBELLES: Record<string, string> = {
  CP: "Code pénal", CCIV: "Code civil", CPC: "Code de procédure civile",
  CPP: "Code de procédure pénale", CTRAV: "Code du travail", CCOM: "Code de commerce",
};

export default function NotificationsPanel({ onFermer }: NotificationsPanelProps) {
  const { t } = useTranslation();
  const conteneurRef = useRef<HTMLDivElement>(null);
  const notifications = useAppStore((s) => s.notificationsVeille);
  const dossiers = useAppStore((s) => s.dossiers);
  const acquitterAlerteJurisprudence = useAppStore((s) => s.acquitterAlerteJurisprudence);
  const acquitterAlerteLoi = useAppStore((s) => s.acquitterAlerteLoi);
  const chargerNotificationsVeille = useAppStore((s) => s.chargerNotificationsVeille);

  useEffect(() => {
    const onClickDehors = (e: MouseEvent) => {
      if (conteneurRef.current && !conteneurRef.current.contains(e.target as Node)) onFermer();
    };
    document.addEventListener("mousedown", onClickDehors);
    return () => document.removeEventListener("mousedown", onClickDehors);
  }, [onFermer]);

  const nomDossier = (id: number) => dossiers.find((d) => d.id === id)?.nom ?? t("generationsPanel.sansDossier");
  const total = notifications.jurisprudence.length + notifications.lois.length + (notifications.rappel_ohada ? 1 : 0);

  return (
    <div ref={conteneurRef} className="absolute right-0 top-full z-30 mt-2 w-96 rounded-md border border-gold-600/25 bg-surface-2 shadow-card">
      <div className="border-b border-gold-600/15 px-3 py-2">
        <p className="text-xs font-medium text-warmgray">{t("notificationsPanel.titre")}</p>
      </div>
      <ul className="max-h-96 overflow-y-auto p-1">
        {notifications.jurisprudence.map((a) => (
          <li key={`jp-${a.id}`} className="rounded-md px-2.5 py-2 text-sm hover:bg-surface">
            <div className="flex items-start gap-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-ivory">📁 {nomDossier(a.dossier_id)}</p>
                <p className="truncate text-xs text-warmgray">{a.reference}</p>
                {a.resume && <p className="mt-0.5 line-clamp-2 text-xs text-muted">{a.resume}</p>}
                {a.source && (
                  <a href={a.source} target="_blank" rel="noreferrer" className="text-xs text-amethyst-400 hover:underline">
                    {t("notificationsPanel.source")}
                  </a>
                )}
              </div>
              <button
                onClick={() => void acquitterAlerteJurisprudence(a.id)}
                className="shrink-0 rounded-md px-2 py-1 text-xs text-muted hover:text-ivory"
              >
                {t("notificationsPanel.vu")}
              </button>
            </div>
          </li>
        ))}

        {notifications.lois.map((a) => (
          <li key={`loi-${a.id}`} className="rounded-md px-2.5 py-2 text-sm hover:bg-surface">
            <div className="flex items-start gap-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-ivory">
                  ⚠️ {t("notificationsPanel.articleModifie", { numero: a.numero, code: CODES_LIBELLES[a.code] ?? a.code })}
                </p>
                <p className="text-xs text-warmgray">📁 {nomDossier(a.dossier_id)}</p>
                <p className="text-xs text-muted">{a.ancien_etat ?? "?"} → {a.nouvel_etat ?? "?"}</p>
                {a.lien_source && (
                  <a href={a.lien_source} target="_blank" rel="noreferrer" className="text-xs text-amethyst-400 hover:underline">
                    {t("notificationsPanel.voirAJour")}
                  </a>
                )}
              </div>
              <button
                onClick={() => void acquitterAlerteLoi(a.id)}
                className="shrink-0 rounded-md px-2 py-1 text-xs text-muted hover:text-ivory"
              >
                {t("notificationsPanel.vu")}
              </button>
            </div>
          </li>
        ))}

        {notifications.rappel_ohada && (
          <li className="rounded-md px-2.5 py-2 text-sm hover:bg-surface">
            <div className="flex items-start gap-2">
              <p className="min-w-0 flex-1 text-xs text-muted">📚 {notifications.rappel_ohada}</p>
              <button
                onClick={() => {
                  void veilleApi.marquerOhadaVerifie().then(() => chargerNotificationsVeille());
                }}
                className="shrink-0 rounded-md px-2 py-1 text-xs text-muted hover:text-ivory"
              >
                {t("notificationsPanel.marquerVerifie")}
              </button>
            </div>
          </li>
        )}

        {total === 0 && <li className="px-2.5 py-3 text-sm text-warmgray">{t("notificationsPanel.vide")}</li>}
      </ul>
    </div>
  );
}
