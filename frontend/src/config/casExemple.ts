/**
 * casExemple.ts — Cas d'exemple optionnel proposé dans NouveauDossierModal
 * ("Pré-remplir avec un cas d'exemple") pour qu'un nouvel utilisateur
 * découvre les fonctionnalités de Plaid'IA (analyse, plan de plaidoirie,
 * simulateur d'objections...) sur un dossier réaliste déjà rempli, sans
 * avoir à saisir ses propres données dès sa première utilisation.
 *
 * Contenu entièrement fictif : librement inspiré dans sa structure d'une
 * affaire criminelle réelle rapportée par la presse, mais noms, date, lieu
 * et détails identifiants ont été changés -- volontairement, pour ne pas
 * associer une vraie personne (accusée ou victime) à des contenus générés
 * par l'IA (argumentaire de défense, simulateur d'objections, score de
 * risque...) à visée persuasive. Voir demo_data.py côté backend pour le
 * même principe appliqué au dossier de démonstration public.
 *
 * Usage strictement optionnel : ce cas ne s'insère nulle part
 * automatiquement, il ne remplit le formulaire que si l'utilisateur clique
 * explicitement sur le bouton dédié dans NouveauDossierModal -- rien n'est
 * créé tant qu'il ne valide pas lui-même le formulaire, exactement comme
 * pour un dossier saisi à la main.
 */

export interface CasExemple {
  nom: string;
  numeroDossier: string;
  domaine: string;
  faits: string;
  stadeProcedure: string;
  objectif: string;
}

export const CAS_EXEMPLE_PENAL: CasExemple = {
  nom: "Affaire Lorrain (cas d'exemple)",
  numeroDossier: "Cas d'exemple — aucune portée réelle",
  domaine: "Pénal",
  // Les parties (accusé, coaccusés, victime) sont nommées dans le récit des
  // faits ci-dessous -- aucune page de l'app n'a de champ "parties" séparé
  // à ce jour, seule la fiche du dossier l'affiche s'il est rempli via
  // l'API (voir DOSSIER_DEMO côté backend, qui l'utilise directement).
  faits:
    "Le 14 novembre 2023, vers 4h50 du matin, une jeep se gare devant Le Verlaine, un bar du " +
    "quartier de Saint-Germain-des-Prés à Paris. Deux hommes en descendent, MM. Kévin Lorrain et " +
    "Julien Fabre, tous deux anciens membres d'un groupuscule d'extrême droite dissous par le " +
    "gouvernement quelques années plus tôt. Ils s'installent en terrasse avec Mme Manon R., " +
    "accompagnatrice de M. Lorrain.\n\n" +
    "Peu après, deux anciens joueurs de rugby, MM. Diego Ferreira (originaire du Brésil) et Liam " +
    "Novak (originaire d'Australie), s'attablent à leur tour à proximité. Vers 5h50, un différend " +
    "éclate : un client aurait demandé une cigarette au groupe de M. Lorrain et se serait fait " +
    "éconduire vivement ; M. Novak serait intervenu pour défendre ce client. Un échange sur " +
    "l'origine des deux rugbymen dégénère, M. Lorrain se levant pour confronter M. Ferreira, se " +
    "présentant comme ancien militaire des forces spéciales et le saisissant par la nuque. Le " +
    "personnel du bar sépare les deux hommes.\n\n" +
    "À la fermeture, vers 6h, M. Ferreira tire M. Lorrain par la capuche en le croisant ; une " +
    "bagarre générale éclate entre les deux groupes, à nouveau interrompue par le personnel. M. " +
    "Lorrain, très agité, menace de tuer M. Ferreira. Plusieurs témoins rapportent qu'il aurait " +
    "exhibé une arme de poing et un brassard de police. Le personnel laisse néanmoins repartir MM. " +
    "Lorrain et Fabre, qui se lancent alors à la recherche des deux rugbymen -- M. Lorrain à pied " +
    "en courant, M. Fabre en voiture conduite par Mme R.\n\n" +
    "Vers 6h07, alors que MM. Ferreira et Novak ressortent d'un hôtel voisin où ils étaient allés " +
    "chercher de la glace pour soigner leurs blessures, le véhicule conduit par Mme R. s'arrête à " +
    "leur hauteur. M. Fabre en descend, sort une arme et fait feu à quatre reprises, blessant M. " +
    "Ferreira. Il prend ensuite la fuite avec Mme R. Une minute plus tard, M. Lorrain, alerté par " +
    "les coups de feu, arrive en courant sur les lieux, se jette sur M. Ferreira et une nouvelle " +
    "altercation éclate. M. Lorrain sort à son tour une arme et tire à quatre reprises, blessant " +
    "mortellement M. Ferreira, qui décède des suites de ses blessures.\n\n" +
    "M. Lorrain prend la fuite, se débarrasse de son arme, puis quitte le territoire français dans " +
    "les jours suivants ; il sera interpellé une semaine plus tard à un poste-frontière d'Europe de " +
    "l'Est, au volant d'un véhicule immatriculé à l'étranger. M. Fabre sera arrêté peu après à son " +
    "domicile. Les perquisitions menées chez les deux hommes révèlent la présence d'armes, de " +
    "munitions en grand nombre et de documents à caractère idéologique d'extrême droite.\n\n" +
    "M. Lorrain, qui invoque la légitime défense, est renvoyé devant la cour criminelle pour " +
    "assassinat -- l'accusation estimant que son arme était chargée avant l'altercation et que sa " +
    "fuite immédiate est incompatible avec cette qualification. M. Fabre est renvoyé pour tentative " +
    "d'assassinat, Mme R. pour complicité de tentative d'assassinat. MM. Lorrain et Fabre ont déjà " +
    "été condamnés par le passé à des peines de prison ferme pour l'agression violente d'un ancien " +
    "responsable de leur groupuscule.\n\n" +
    "[Cas d'exemple — contenu fictif librement inspiré d'un fait divers, destiné uniquement à " +
    "s'entraîner à l'usage de Plaid'IA. Toute ressemblance avec une affaire réelle serait fortuite.]",
  stadeProcedure: "Première instance",
  objectif:
    "Cas d'exemple : explorez librement les fonctionnalités de Plaid'IA (analyse de conclusions " +
    "adverses, plan de plaidoirie, simulateur d'objections, chronologie...) sur ce dossier fictif, " +
    "en choisissant vous-même la partie que vous souhaitez représenter ci-dessus.",
};
