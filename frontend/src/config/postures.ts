export const STADES_PROCEDURE = ["Première instance", "Appel", "Cassation"];

export function posturesPourDomaine(domaine: string): string[] {
  if (domaine === "Pénal") return ["Prévenu", "Accusé", "Mis en examen", "Partie civile", "Ministère public"];
  if (domaine === "Prud'hommes") return ["Employeur", "Salarié"];
  if (domaine === "OHADA" || domaine === "Commercial") return ["Demandeur", "Défendeur", "Créancier", "Débiteur"];
  if (domaine === "Administratif") return ["Requérant", "Administration défenderesse"];
  if (domaine === "Social") return ["Assuré", "Organisme social"];
  return ["Demandeur", "Défendeur", "Autre"];
}
