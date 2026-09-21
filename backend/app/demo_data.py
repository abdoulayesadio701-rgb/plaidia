"""
demo_data.py — Contenu préenregistré du mode démo (voir demo.py) : un
dossier fictif de droit du travail ("Diallo c/ Atlas Logistique") avec son
analyse de conclusions adverses, son plan de plaidoirie, son simulateur
d'objections et sa chronologie -- au format exact des schémas Pydantic
correspondants, pour que le front n'ait strictement rien à distinguer entre
une réponse démo et une réponse réelle.

Toute ressemblance avec une affaire réelle est fortuite : noms, dates et
pièces sont inventés pour l'exercice.

Chaque jeu de données existe en FR et en EN (suffixes _FR/_EN) et se
sélectionne via analyse.langue_requete() (posé par le middleware X-Langue de
main.py), à l'exception de DOSSIER_DEMO : contrairement aux autres, ce
dossier est ensemencé UNE SEULE FOIS en base au démarrage du serveur (voir
main.py::lifespan), partagé par tous les visiteurs -- il ne peut donc pas
varier selon la langue de la requête courante, faute de quoi son contenu
changerait de langue sous les pieds d'un visiteur déjà en train de le
consulter. Les constantes sans suffixe (CONCLUSIONS_DEMO, PLAN_DEMO, ...)
restent exportées pour compatibilité ascendante -- toujours la version
française -- mais le code applicatif doit passer par les fonctions
conclusions_demo()/plan_demo()/simulateur_demo()/chronologie_demo()/
resume_demo() ci-dessous, jamais les constantes directement.
"""

import analyse as legacy_analyse

NOM_DOSSIER_DEMO = "Diallo c/ Atlas Logistique"

DOSSIER_DEMO = {
    "nom": NOM_DOSSIER_DEMO,
    "numero_dossier": "RG 24/01187 (démonstration)",
    "domaine": "Prud'hommes",
    "parties": "M. Karim Diallo (demandeur, salarié) c/ SAS Atlas Logistique (défenderesse, employeur)",
    "faits": (
        "M. Karim Diallo, magasinier-cariste, a été engagé le 3 juin 2019 par la SAS Atlas Logistique "
        "(Bondy, 93) en contrat à durée indéterminée. Le 14 février 2024, il est convoqué à un entretien "
        "préalable à un licenciement pour faute grave, notifié le 28 février 2024. L'employeur invoque "
        "trois retards consécutifs (5, 8 et 9 février 2024) ainsi qu'un refus d'obtempérer face à son "
        "supérieur hiérarchique le 9 février. M. Diallo conteste les faits : les retards seraient liés à "
        "un mouvement de grève sur la ligne RER B, et l'échange du 9 février relèverait d'un désaccord "
        "verbal sur une réaffectation de poste, non d'une insubordination caractérisée. Il n'a fait "
        "l'objet d'aucun avertissement en cinq ans d'ancienneté. Il saisit le conseil de prud'hommes de "
        "Bobigny en contestation du licenciement et sollicite sa requalification en licenciement sans "
        "cause réelle et sérieuse, ainsi que des dommages et intérêts.\n\n"
        "[Dossier de démonstration — contenu entièrement fictif, généré pour illustrer Plaid'IA.]"
    ),
    "statut": "en cours",
}

CONCLUSIONS_DEMO_FR = {
    "arguments": [
        {
            "resume": "Les trois retards des 5, 8 et 9 février 2024 caractérisent un manquement réitéré à l'obligation de ponctualité.",
            "fondement": "Relevé de badgeuse produit en pièce 4 par l'employeur, faisant état de trois retards de 22 à 41 minutes sur la période du 5 au 9 février 2024.",
            "raisonnement": {
                "probleme_de_droit": "Des retards répétés, même de courte durée, peuvent-ils à eux seuls caractériser une faute grave justifiant un licenciement sans préavis ni indemnité ?",
                "regle_applicable": "La faute grave suppose un manquement rendant impossible le maintien du salarié dans l'entreprise pendant la durée du préavis. [VERIF:la qualification retenue par la jurisprudence pour des retards isolés sans avertissement préalable]",
                "application_aux_faits": "M. Diallo n'a fait l'objet d'aucune sanction disciplinaire en cinq ans d'ancienneté ; les trois retards invoqués sont concentrés sur une semaine coïncidant avec un mouvement de grève RER B (pièce 7), ce qui affaiblit sensiblement le caractère fautif et délibéré retenu par l'employeur.",
            },
            "risque": "Moyen",
            "justification_risque": "L'absence de tout antécédent disciplinaire et la coïncidence avec une grève des transports fragilisent la qualification de faute grave, sans l'exclure totalement si l'employeur démontre qu'un trajet alternatif était raisonnablement praticable.",
            "refutations": [
                {"angle": "Factuel", "piste": "Produire l'attestation SNCF/RATP de perturbation du trafic sur la ligne empruntée par M. Diallo aux dates visées."},
                {"angle": "Juridique", "piste": "[VERIF:rechercher un arrêt de la chambre sociale excluant la faute grave en cas de retards liés à un mouvement de grève des transports]"},
            ],
        },
        {
            "resume": "Le refus d'obtempérer du 9 février 2024 face à M. Bertrand, chef d'équipe, constitue un acte d'insubordination caractérisée.",
            "fondement": "Attestation de M. Bertrand (pièce 6) selon laquelle M. Diallo aurait « refusé catégoriquement » de reprendre le poste de conditionnement qui lui était assigné.",
            "raisonnement": {
                "probleme_de_droit": "Un désaccord ponctuel sur l'affectation d'un poste, exprimé verbalement, suffit-il à caractériser une insubordination fautive ?",
                "regle_applicable": "L'insubordination suppose un refus délibéré et injustifié d'exécuter une instruction relevant du pouvoir de direction de l'employeur, appréciée au regard du contexte et de la teneur exacte des propos échangés.",
                "application_aux_faits": "Une seule attestation, non corroborée, émanant du supérieur hiérarchique directement impliqué dans le désaccord, ne permet pas d'établir avec certitude la teneur exacte des propos échangés ni leur caractère délibérément insubordonné plutôt qu'un désaccord ponctuel sur une réaffectation non prévue au contrat.",
            },
            "risque": "Faible",
            "justification_risque": "La preuve repose sur un témoignage unique et non corroboré d'une partie elle-même impliquée dans l'échange contesté, ce qui affaiblit fortement la force probante de cet argument.",
            "refutations": [
                {"angle": "Factuel", "piste": "Solliciter l'attestation de collègues présents lors de l'échange du 9 février pour contredire ou nuancer la version de M. Bertrand."},
                {"angle": "Proportionnalité", "piste": "Souligner qu'à supposer les faits établis, un désaccord verbal isolé ne justifie pas, à lui seul et sans réitération, une rupture immédiate du contrat sans préavis."},
            ],
        },
        {
            "resume": "L'ancienneté du salarié ne fait pas obstacle à la qualification de faute grave dès lors que les faits sont établis.",
            "fondement": "Argument de principe soulevé par l'employeur en réponse à l'absence d'antécédents disciplinaires de M. Diallo.",
            "raisonnement": {
                "probleme_de_droit": "L'ancienneté et l'absence de tout antécédent disciplinaire doivent-elles être prises en compte dans l'appréciation de la gravité de la faute reprochée ?",
                "regle_applicable": "[VERIF:la jurisprudence sociale intègre traditionnellement l'ancienneté et le comportement antérieur du salarié parmi les éléments d'appréciation de la gravité d'un manquement, sans que ce soit un obstacle absolu]",
                "application_aux_faits": "Si l'ancienneté n'exclut pas par principe la faute grave, cinq années sans le moindre incident constituent un élément de contexte que le conseil de prud'hommes pondérera nécessairement face à des faits eux-mêmes contestés dans leur matérialité et leur gravité.",
            },
            "risque": "Faible",
            "justification_risque": "L'argument de l'employeur est recevable en droit mais peu opérant en l'espèce dès lors que la matérialité et la gravité des faits reprochés sont elles-mêmes fragiles.",
            "refutations": [
                {"angle": "Juridique", "piste": "Rappeler que l'ancienneté et l'absence d'antécédent, sans être décisifs à eux seuls, sont systématiquement pris en compte dans l'appréciation globale de la proportionnalité de la sanction."},
            ],
        },
    ],
    "points_attention": [
        "Vérifier si l'entretien préalable a respecté le délai légal avant la notification du licenciement (élément non précisé dans les pièces transmises).",
        "L'employeur pourrait produire des pièces complémentaires (autres témoignages, historique de badgeuse plus large) non communiquées à ce stade — à anticiper.",
    ],
}

CONCLUSIONS_DEMO_EN = {
    "arguments": [
        {
            "resume": "The three instances of lateness on 5, 8 and 9 February 2024 show a repeated failure to meet the duty of punctuality.",
            "fondement": "Time-clock record submitted as exhibit 4 by the employer, showing three instances of lateness of 22 to 41 minutes over the period from 5 to 9 February 2024.",
            "raisonnement": {
                "probleme_de_droit": "Can repeated instances of lateness, even brief ones, on their own amount to serious misconduct justifying dismissal without notice or severance pay?",
                "regle_applicable": "Serious misconduct requires a failure that makes it impossible to keep the employee on during the notice period. [VERIF:the qualification applied by case law to isolated instances of lateness with no prior warning]",
                "application_aux_faits": "Mr. Diallo has faced no disciplinary sanction in five years of tenure; the three instances of lateness relied upon are concentrated within one week coinciding with an RER B rail strike (exhibit 7), which significantly weakens the wrongful and deliberate character claimed by the employer.",
            },
            "risque": "Moyen",
            "justification_risque": "The absence of any disciplinary record and the coincidence with a transport strike weaken the case for serious misconduct, without ruling it out entirely if the employer shows that a reasonable alternative route was available.",
            "refutations": [
                {"angle": "Factuel", "piste": "Produce the SNCF/RATP certificate confirming the traffic disruption on the line used by Mr. Diallo on the dates in question."},
                {"angle": "Juridique", "piste": "[VERIF:find a ruling from the labour chamber excluding serious misconduct in the case of lateness linked to a transport strike]"},
            ],
        },
        {
            "resume": "The refusal to comply on 9 February 2024 towards Mr. Bertrand, team leader, constitutes a clear act of insubordination.",
            "fondement": "Statement from Mr. Bertrand (exhibit 6) stating that Mr. Diallo \"categorically refused\" to return to the packing station he had been assigned.",
            "raisonnement": {
                "probleme_de_droit": "Is a one-off, verbally expressed disagreement over a job assignment enough to amount to wrongful insubordination?",
                "regle_applicable": "Insubordination requires a deliberate and unjustified refusal to carry out an instruction falling within the employer's managerial authority, assessed in light of the context and the exact content of the words exchanged.",
                "application_aux_faits": "A single, uncorroborated statement from the direct superior involved in the disagreement does not establish with certainty either the exact content of the words exchanged or their deliberately insubordinate character rather than a one-off disagreement over an unplanned reassignment.",
            },
            "risque": "Faible",
            "justification_risque": "The evidence rests on a single, uncorroborated testimony from a party itself involved in the disputed exchange, which strongly weakens the probative value of this argument.",
            "refutations": [
                {"angle": "Factuel", "piste": "Seek statements from colleagues present during the exchange on 9 February to contradict or qualify Mr. Bertrand's account."},
                {"angle": "Proportionnalité", "piste": "Point out that, even assuming the facts are established, an isolated verbal disagreement does not, on its own and without repetition, justify an immediate termination of the contract without notice."},
            ],
        },
        {
            "resume": "The employee's seniority does not preclude a finding of serious misconduct once the facts are established.",
            "fondement": "Argument of principle raised by the employer in response to the absence of any disciplinary record for Mr. Diallo.",
            "raisonnement": {
                "probleme_de_droit": "Should seniority and the absence of any disciplinary record be taken into account when assessing the seriousness of the misconduct alleged?",
                "regle_applicable": "[VERIF:labour case law traditionally factors in seniority and the employee's prior conduct among the elements used to assess the seriousness of a failure, without this being an absolute bar]",
                "application_aux_faits": "While seniority does not in principle rule out serious misconduct, five years without a single incident is a contextual element the labour tribunal will necessarily weigh against facts whose substance and seriousness are themselves disputed.",
            },
            "risque": "Faible",
            "justification_risque": "The employer's argument is legally admissible but of little practical weight here, given that the substance and seriousness of the alleged facts are themselves shaky.",
            "refutations": [
                {"angle": "Juridique", "piste": "Recall that seniority and the absence of a disciplinary record, while not decisive on their own, are systematically taken into account in the overall assessment of the proportionality of the sanction."},
            ],
        },
    ],
    "points_attention": [
        "Check whether the preliminary meeting complied with the statutory time limit before the dismissal notice (not specified in the documents provided).",
        "The employer could produce further evidence (other testimony, a broader time-clock history) not disclosed at this stage — to anticipate.",
    ],
}

# Rétro-compatibilité (toujours la version française) -- voir l'en-tête du fichier.
CONCLUSIONS_DEMO = CONCLUSIONS_DEMO_FR


def conclusions_demo() -> dict:
    return CONCLUSIONS_DEMO_EN if legacy_analyse.langue_requete() == "en" else CONCLUSIONS_DEMO_FR


PLAN_DEMO_FR = {
    "accroche": (
        "Monsieur le Président, Mesdames et Messieurs les conseillers, cinq années de service sans le "
        "moindre reproche, balayées en quelques jours, pour trois retards liés à une grève des transports "
        "et un désaccord verbal rapporté par un témoin unique : voilà ce que nous vous demandons "
        "d'apprécier aujourd'hui."
    ),
    "plan": [
        {
            "point": "Rappel des faits et de la relation de travail",
            "duree_minutes": 2,
            "argument_cle": "Cinq ans d'ancienneté, aucun antécédent disciplinaire, licenciement notifié en quelques jours.",
            "notes": "Insister sur le contraste entre l'ancienneté et la brutalité de la rupture.",
        },
        {
            "point": "Sur les retards des 5, 8 et 9 février 2024",
            "duree_minutes": 4,
            "argument_cle": "Ces retards coïncident avec un mouvement de grève RER B, établi par pièce.",
            "notes": "Présenter la pièce 7 (communiqué SNCF) avant toute discussion sur la matérialité des retards.",
        },
        {
            "point": "Sur le prétendu refus d'obtempérer du 9 février",
            "duree_minutes": 4,
            "argument_cle": "La preuve repose sur le témoignage unique et non corroboré de la personne impliquée dans le désaccord.",
            "notes": "Souligner l'absence de tout autre témoin cité par l'employeur malgré un atelier de douze personnes.",
        },
        {
            "point": "Sur la disproportion de la sanction au regard de l'ancienneté",
            "duree_minutes": 3,
            "argument_cle": "Aucune mesure intermédiaire (avertissement, mise à pied) n'a été envisagée avant la rupture immédiate.",
            "notes": "Rappeler l'échelle des sanctions prévue par le règlement intérieur, si versé aux débats.",
        },
        {
            "point": "Sur les conséquences : requalification et indemnisation",
            "duree_minutes": 2,
            "argument_cle": "Demande de requalification en licenciement sans cause réelle et sérieuse et indemnisation du préjudice subi.",
            "notes": "Chiffrer précisément le préjudice avant l'audience selon l'ancienneté.",
        },
    ],
    "conclusion": (
        "La faute grave qui prive un salarié de son préavis et de son indemnité de licenciement exige une "
        "certitude que ce dossier ne présente pas. Le doute, ici, doit profiter à cinq années de loyaux "
        "services."
    ),
    "points_attention": [
        "Préparer une réponse orale si l'employeur produit à l'audience des pièces non communiquées.",
        "Vérifier la présence effective de M. Diallo à l'audience pour un éventuel interrogatoire.",
    ],
}

PLAN_DEMO_EN = {
    "accroche": (
        "Mr. President, Members of the tribunal, five years of service without a single reproach, swept "
        "aside in a matter of days, over three instances of lateness linked to a transport strike and a "
        "verbal disagreement reported by a single witness: this is what we ask you to weigh today."
    ),
    "plan": [
        {
            "point": "Recap of the facts and the employment relationship",
            "duree_minutes": 2,
            "argument_cle": "Five years of tenure, no disciplinary record, dismissal notified within days.",
            "notes": "Stress the contrast between the seniority and the abruptness of the termination.",
        },
        {
            "point": "On the instances of lateness on 5, 8 and 9 February 2024",
            "duree_minutes": 4,
            "argument_cle": "These instances of lateness coincide with an RER B rail strike, established by exhibit.",
            "notes": "Present exhibit 7 (SNCF notice) before any discussion of whether the lateness actually occurred.",
        },
        {
            "point": "On the alleged refusal to comply on 9 February",
            "duree_minutes": 4,
            "argument_cle": "The evidence rests on the single, uncorroborated testimony of the person involved in the disagreement.",
            "notes": "Highlight the absence of any other witness cited by the employer despite a workshop of twelve people.",
        },
        {
            "point": "On the disproportion of the sanction given the seniority",
            "duree_minutes": 3,
            "argument_cle": "No intermediate measure (warning, suspension) was considered before the immediate termination.",
            "notes": "Recall the scale of sanctions set out in the internal rules, if filed in evidence.",
        },
        {
            "point": "On the consequences: reclassification and compensation",
            "duree_minutes": 2,
            "argument_cle": "Request to reclassify as a dismissal without real and serious cause, and compensation for the harm suffered.",
            "notes": "Quantify the harm precisely before the hearing, based on seniority.",
        },
    ],
    "conclusion": (
        "Serious misconduct, which deprives an employee of notice and severance pay, requires a certainty "
        "this case does not present. The doubt here should benefit five years of loyal service."
    ),
    "points_attention": [
        "Prepare an oral response in case the employer produces undisclosed evidence at the hearing.",
        "Check that Mr. Diallo will actually be present at the hearing in case of questioning.",
    ],
}

# Rétro-compatibilité (toujours la version française) -- voir l'en-tête du fichier.
PLAN_DEMO = PLAN_DEMO_FR


def plan_demo() -> dict:
    return PLAN_DEMO_EN if legacy_analyse.langue_requete() == "en" else PLAN_DEMO_FR


SIMULATEUR_DEMO_FR = {
    "objections": [
        {
            "origine": "Partie adverse",
            "question": "Pourquoi votre client n'a-t-il signalé la grève des transports à son employeur qu'après sa convocation à l'entretien préalable ?",
            "piege": "Suggérer que l'explication est une justification a posteriori, inventée pour les besoins de la défense.",
            "piste_reponse": "Produire, si possible, un échange contemporain des faits évoquant déjà ces perturbations ; à défaut, s'appuyer sur la notoriété publique du mouvement de grève (pièce 7), qui rend l'explication crédible indépendamment de tout signalement formel.",
        },
        {
            "origine": "Magistrat",
            "question": "Le règlement intérieur de l'entreprise prévoit-il une tolérance en cas de grève des transports ?",
            "piege": "Aucun règlement intérieur n'a été communiqué à ce stade — une absence de réponse affaiblirait la position du demandeur.",
            "piste_reponse": "Solliciter la communication du règlement intérieur avant l'audience ; à défaut de disposition spécifique, rappeler que l'absence de procédure ne prive pas le salarié du droit d'invoquer les faits.",
        },
        {
            "origine": "Partie adverse",
            "question": "Si les propos du 9 février n'étaient qu'un désaccord anodin, pourquoi votre client ne les a-t-il pas contestés lors de l'entretien préalable ?",
            "piege": "Faire peser sur le silence de M. Diallo lors de l'entretien une présomption d'aveu implicite.",
            "piste_reponse": "Rappeler que l'entretien préalable n'est pas un débat contradictoire mais une formalité procédurale asymétrique, et que le silence du salarié ne vaut jamais reconnaissance des faits. [VERIF:citer un arrêt en ce sens si disponible]",
        },
        {
            "origine": "Magistrat",
            "question": "M. Diallo occupait-il un poste à responsabilité particulière justifiant une exigence de ponctualité renforcée ?",
            "piege": "Faire ressortir un élément du contrat de travail non anticipé par la défense.",
            "piste_reponse": "Vérifier précisément les termes du contrat de travail et de la fiche de poste avant l'audience plutôt que d'y répondre dans l'incertitude.",
        },
    ],
    "point_le_plus_faible": (
        "L'absence, à ce stade du dossier, de toute pièce contemporaine confirmant la version de M. Diallo "
        "sur l'échange du 9 février — la défense repose largement sur la fragilité de la preuve adverse "
        "plutôt que sur une preuve positive propre."
    ),
}

SIMULATEUR_DEMO_EN = {
    "objections": [
        {
            "origine": "Partie adverse",
            "question": "Why did your client only report the transport strike to his employer after being summoned to the preliminary meeting?",
            "piege": "Suggest that the explanation is an after-the-fact justification, invented for the needs of the defence.",
            "piste_reponse": "Produce, if possible, an exchange contemporaneous with the facts already mentioning these disruptions; failing that, rely on the public notoriety of the strike (exhibit 7), which makes the explanation credible independently of any formal report.",
        },
        {
            "origine": "Magistrat",
            "question": "Does the company's internal rules provide for any leniency in the event of a transport strike?",
            "piege": "No internal rules have been disclosed at this stage — a lack of an answer would weaken the claimant's position.",
            "piste_reponse": "Request disclosure of the internal rules before the hearing; failing any specific provision, recall that the absence of a procedure does not deprive the employee of the right to invoke the facts.",
        },
        {
            "origine": "Partie adverse",
            "question": "If the remarks on 9 February were only a trivial disagreement, why did your client not dispute them at the preliminary meeting?",
            "piege": "Treat Mr. Diallo's silence at the meeting as an implicit admission.",
            "piste_reponse": "Recall that the preliminary meeting is not an adversarial debate but an asymmetric procedural formality, and that an employee's silence never amounts to an admission of the facts. [VERIF:cite a ruling to this effect if available]",
        },
        {
            "origine": "Magistrat",
            "question": "Did Mr. Diallo hold a position of particular responsibility justifying a heightened requirement of punctuality?",
            "piege": "Bring out a term of the employment contract not anticipated by the defence.",
            "piste_reponse": "Check the exact terms of the employment contract and job description before the hearing rather than answering while uncertain.",
        },
    ],
    "point_le_plus_faible": (
        "The absence, at this stage of the case, of any evidence contemporaneous with the facts confirming "
        "Mr. Diallo's account of the exchange on 9 February — the defence rests largely on the weakness of "
        "the opposing evidence rather than on positive evidence of its own."
    ),
}

# Rétro-compatibilité (toujours la version française) -- voir l'en-tête du fichier.
SIMULATEUR_DEMO = SIMULATEUR_DEMO_FR


def simulateur_demo() -> dict:
    return SIMULATEUR_DEMO_EN if legacy_analyse.langue_requete() == "en" else SIMULATEUR_DEMO_FR


CHRONOLOGIE_DEMO_FR = {
    "periode_couverte": "3 juin 2019 – 15 avril 2024",
    "evenements": [
        {"date": "3 juin 2019", "evenement": "Embauche de M. Karim Diallo en qualité de magasinier-cariste au sein de la SAS Atlas Logistique (CDI)."},
        {"date": "5 février 2024", "evenement": "Premier retard relevé (22 minutes), coïncidant avec un mouvement de grève sur la ligne RER B."},
        {"date": "8 février 2024", "evenement": "Second retard relevé (35 minutes)."},
        {"date": "9 février 2024", "evenement": "Troisième retard relevé (41 minutes) ; échange contesté avec M. Bertrand, chef d'équipe, sur une réaffectation de poste."},
        {"date": "14 février 2024", "evenement": "Convocation à un entretien préalable au licenciement, remise en main propre."},
        {"date": "21 février 2024", "evenement": "Tenue de l'entretien préalable, en présence d'un conseiller du salarié."},
        {"date": "28 février 2024", "evenement": "Notification du licenciement pour faute grave, avec effet immédiat."},
        {"date": "15 avril 2024", "evenement": "Saisine du conseil de prud'hommes de Bobigny en contestation du licenciement."},
    ],
    "elements_manquants": [
        "Date exacte de réception de la lettre de licenciement par le salarié (fait courir le délai de contestation).",
        "Éventuels échanges écrits entre M. Diallo et sa hiérarchie antérieurs au 5 février 2024.",
    ],
}

CHRONOLOGIE_DEMO_EN = {
    "periode_couverte": "3 June 2019 – 15 April 2024",
    "evenements": [
        {"date": "3 June 2019", "evenement": "Mr. Karim Diallo hired as a warehouse operator/forklift driver by SAS Atlas Logistique (open-ended contract)."},
        {"date": "5 February 2024", "evenement": "First instance of lateness recorded (22 minutes), coinciding with a strike on the RER B line."},
        {"date": "8 February 2024", "evenement": "Second instance of lateness recorded (35 minutes)."},
        {"date": "9 February 2024", "evenement": "Third instance of lateness recorded (41 minutes); disputed exchange with Mr. Bertrand, team leader, over a job reassignment."},
        {"date": "14 February 2024", "evenement": "Summons to a preliminary dismissal meeting, delivered by hand."},
        {"date": "21 February 2024", "evenement": "Preliminary meeting held, in the presence of an employee adviser."},
        {"date": "28 February 2024", "evenement": "Dismissal for serious misconduct notified, with immediate effect."},
        {"date": "15 April 2024", "evenement": "Labour tribunal of Bobigny seized to challenge the dismissal."},
    ],
    "elements_manquants": [
        "Exact date the dismissal letter was received by the employee (starts the time limit to challenge it running).",
        "Any written exchanges between Mr. Diallo and his management before 5 February 2024.",
    ],
}

# Rétro-compatibilité (toujours la version française) -- voir l'en-tête du fichier.
CHRONOLOGIE_DEMO = CHRONOLOGIE_DEMO_FR


def chronologie_demo() -> dict:
    return CHRONOLOGIE_DEMO_EN if legacy_analyse.langue_requete() == "en" else CHRONOLOGIE_DEMO_FR


RESUME_DEMO_FR = {
    "resume_court": (
        "M. Karim Diallo, magasinier-cariste depuis 2019 chez Atlas Logistique, conteste son licenciement "
        "pour faute grave notifié le 28 février 2024, motivé par trois retards imputés à une grève des "
        "transports et un désaccord verbal avec son chef d'équipe rapporté par un témoin unique. Il "
        "sollicite la requalification en licenciement sans cause réelle et sérieuse."
    ),
    "points_cles": [
        "Cinq années d'ancienneté sans aucun antécédent disciplinaire.",
        "Les trois retards invoqués coïncident avec un mouvement de grève RER B documenté (pièce 7).",
        "L'accusation d'insubordination repose sur le témoignage unique et non corroboré du supérieur hiérarchique impliqué.",
        "Aucune sanction intermédiaire n'a été envisagée avant la rupture immédiate du contrat.",
    ],
    "elements_manquants": [
        "Règlement intérieur de l'entreprise (procédure éventuelle en cas de perturbation des transports).",
        "Contrat de travail et fiche de poste précisant les exigences de ponctualité.",
        "Pièces complémentaires susceptibles d'être produites par l'employeur en cours de procédure.",
    ],
}

RESUME_DEMO_EN = {
    "resume_court": (
        "Mr. Karim Diallo, a warehouse operator/forklift driver at Atlas Logistique since 2019, is "
        "challenging his dismissal for serious misconduct notified on 28 February 2024, based on three "
        "instances of lateness attributed to a transport strike and a verbal disagreement with his team "
        "leader reported by a single witness. He is seeking reclassification as a dismissal without real "
        "and serious cause."
    ),
    "points_cles": [
        "Five years of tenure with no disciplinary record whatsoever.",
        "The three instances of lateness relied upon coincide with a documented RER B rail strike (exhibit 7).",
        "The insubordination accusation rests on the single, uncorroborated testimony of the superior involved.",
        "No intermediate sanction was considered before the immediate termination of the contract.",
    ],
    "elements_manquants": [
        "The company's internal rules (any procedure for transport disruptions).",
        "Employment contract and job description specifying the punctuality requirements.",
        "Further evidence the employer might produce during the proceedings.",
    ],
}

# Rétro-compatibilité (toujours la version française) -- voir l'en-tête du fichier.
RESUME_DEMO = RESUME_DEMO_FR


def resume_demo() -> dict:
    return RESUME_DEMO_EN if legacy_analyse.langue_requete() == "en" else RESUME_DEMO_FR


# --- Chat : quelques réponses préenregistrées selon des mots-clés simples,
# et une réponse générique par défaut qui oriente vers les actions cannées
# ci-dessus. Chacune conserve une balise [VERIF:...] (ou [ART:...]) pour
# démontrer le balisage anti-hallucination même en mode démo -- voir
# analyse.REGLE_BALISAGE_CITATIONS.
#
# Seul le chat (contrairement aux autres actions démo de ce fichier) tient
# compte de la langue d'interface : chaque réponse existe en FR et en EN
# (voir analyse.langue_requete(), posé par le middleware X-Langue de
# main.py), sélectionnée par _REPONSES_CHAT_PAR_LANGUE ci-dessous.

REPONSE_CHAT_DEFAUT_FR = """Vous êtes en **mode démo** de Plaid'IA : aucune clé API n'est configurée sur ce serveur public, je ne peux donc pas traiter librement une question ici.

Ce que vous pouvez explorer dès maintenant, avec des données réalistes préenregistrées sur le dossier de démonstration « Diallo c/ Atlas Logistique » :
- **Analyser des conclusions adverses**
- **Générer un plan de plaidoirie** chronométré
- **Simuler les objections** probables du magistrat ou de la partie adverse
- **Construire sa chronologie** automatique

Pour poser une vraie question et obtenir une réponse générée en direct, utilisez **« Utiliser ma propre clé Anthropic »** en pied de page — votre clé reste dans votre navigateur et n'est jamais journalisée par le serveur.

[VERIF:comme toute réponse de Plaid'IA, même hors mode démo, ceci resterait à vérifier avant tout usage professionnel — c'est tout l'esprit de ce garde-fou]."""

REPONSE_CHAT_FAUTE_GRAVE_FR = """Dans le dossier de démonstration (Diallo c/ Atlas Logistique), la qualification de faute grave retenue par l'employeur repose sur des retards répétés et un incident d'insubordination.

En droit du travail français, la faute grave est celle qui rend impossible le maintien du salarié dans l'entreprise, même pendant la durée du préavis : elle prive le salarié de son préavis et de son indemnité de licenciement.

Deux éléments fragilisent cette qualification dans les faits présentés ici :
- l'absence de tout antécédent disciplinaire en cinq ans d'ancienneté ;
- la coïncidence des retards avec un mouvement de grève des transports en commun.

[VERIF:la position de la jurisprudence de la chambre sociale sur la prise en compte des perturbations de transport dans l'appréciation de la faute grave]

*Réponse préenregistrée du mode démo, illustrant le format habituel de l'agent — pas une analyse en direct de votre situation.*"""

REPONSE_CHAT_DELAI_FR = """Sur le plan procédural, une contestation de licenciement devant le conseil de prud'hommes doit en principe être introduite dans un délai de 12 mois à compter de la notification du licenciement ([ART:L.1471-1:CTRAV]).

[VERIF:ce délai peut varier selon la nature exacte du grief invoqué (discrimination, harcèlement...) — à confirmer au cas par cas]

Dans le dossier de démonstration, le licenciement a été notifié le 28 février 2024 et la saisine du conseil de prud'hommes est intervenue le 15 avril 2024 — largement dans les délais.

*Réponse préenregistrée du mode démo.*"""

REPONSE_CHAT_DEFAUT_EN = """You are in Plaid'IA's **demo mode**: no API key is configured on this public server, so I can't freely process a question here.

What you can explore right now, with realistic prerecorded data on the demonstration case "Diallo v. Atlas Logistique":
- **Analyse opposing submissions**
- **Generate a timed pleading plan**
- **Simulate** the judge's or opposing party's likely **objections**
- **Build its automatic timeline**

To ask a real question and get a live-generated answer, use **"Use my own Anthropic key"** at the bottom of the page — your key stays in your browser and is never logged by the server.

[VERIF:like any Plaid'IA answer, even outside demo mode, this would still need to be checked before any professional use — that's the whole point of this safeguard]."""

REPONSE_CHAT_FAUTE_GRAVE_EN = """In the demonstration case (Diallo v. Atlas Logistique), the serious misconduct claimed by the employer rests on repeated lateness and an insubordination incident.

Under French employment law, serious misconduct ("faute grave") is a failure that makes it impossible to keep the employee on even during the notice period: it deprives the employee of both notice and severance pay.

Two elements weaken this qualification in the facts presented here:
- the absence of any prior disciplinary record in five years of tenure;
- the coincidence of the lateness with a public transport strike.

[VERIF:the case law position of the labour chamber on taking transport disruptions into account when assessing serious misconduct]

*Prerecorded demo-mode answer, illustrating the agent's usual format — not a live analysis of your own situation.*"""

REPONSE_CHAT_DELAI_EN = """Procedurally, a challenge to a dismissal before the labour tribunal (conseil de prud'hommes) must in principle be filed within 12 months of the dismissal notice ([ART:L.1471-1:CTRAV]).

[VERIF:this time limit can vary depending on the exact nature of the claim raised (discrimination, harassment...) — to be confirmed case by case]

In the demonstration case, the dismissal was notified on 28 February 2024 and the labour tribunal was seized on 15 April 2024 — well within the time limit.

*Prerecorded demo-mode answer.*"""

REPONSE_CHAT_RESPONSABILITE_FR = """L'article 1240 du Code civil pose le principe de la **responsabilité civile délictuelle** : « tout fait quelconque de l'homme, qui cause à autrui un dommage, oblige celui par la faute duquel il est arrivé à le réparer » ([ART:1240:CCIV]). L'article suivant précise que la faute inclut la négligence et l'imprudence ([ART:1241:CCIV]).

Trois conditions doivent être réunies :
- **une faute** : un comportement que n'aurait pas eu une personne raisonnable placée dans les mêmes circonstances ;
- **un dommage** : un préjudice certain, qu'il soit matériel, corporel ou moral ;
- **un lien de causalité** entre la faute et le dommage.

Il appartient en principe à la victime de prouver ces trois éléments ([ART:1353:CCIV]). L'action se prescrit par cinq ans à compter du jour où la victime a connu, ou aurait dû connaître, les faits lui permettant de l'exercer ([ART:2224:CCIV]).

[VERIF:les règles de prescription et de preuve applicables varient selon le type de dommage (corporel, environnemental...) et selon qu'un régime spécial de responsabilité s'applique — à confirmer au cas par cas]

[VERIF:la position de la Cour de cassation sur l'appréciation du lien de causalité en cas de causes multiples]

*Réponse préenregistrée du mode démo, illustrant le format habituel de l'agent (balisage des citations, points à vérifier) — pas une analyse en direct de votre situation.*"""

REPONSE_CHAT_PLAIDOIRIE_FR = """Voici la structure classique d'une plaidoirie civile de 10 minutes, avec un chronométrage indicatif :

1. **Exorde (1 min)** : poser la question centrale du litige en une phrase, et annoncer le plan.
2. **Exposé des faits (2 min)** : ne retenir que les faits utiles à la démonstration, dans l'ordre chronologique, sans qualification juridique prématurée.
3. **Discussion (5 min)** : hiérarchiser les moyens.
   - d'abord les moyens de procédure et les fins de non-recevoir, qui empêchent l'examen du fond ([ART:122:CPC]) ;
   - puis les moyens de fond, du plus solide au plus fragile, chacun suivi de sa preuve ([ART:9:CPC]).
4. **Réfutation (1 min)** : répondre aux deux ou trois arguments adverses les plus dangereux.
5. **Dispositif (1 min)** : rappeler précisément ce qui est demandé au tribunal.

Un conseil de méthode : n'annoncer que ce que l'on démontrera vraiment, et garder le meilleur argument pour la fin de la discussion.

[VERIF:le temps de parole réellement alloué dépend de la juridiction, de la nature de l'audience et de la pratique du magistrat — à confirmer avant l'audience]

Pour obtenir un plan chronométré complet, avec les arguments et les pièces du dossier, utilisez **« Générer un plan de plaidoirie »** sur le dossier de démonstration « Diallo c/ Atlas Logistique ».

*Réponse préenregistrée du mode démo.*"""

REPONSE_CHAT_RESPONSABILITE_EN = """Article 1240 of the French Civil Code sets out the principle of **tort liability** (responsabilité civile délictuelle): "any act whatsoever of a person which causes damage to another obliges the person by whose fault it occurred to make reparation" ([ART:1240:CCIV]). The following article clarifies that fault includes negligence and imprudence ([ART:1241:CCIV]).

Three conditions must be met:
- **a fault**: conduct that a reasonable person placed in the same circumstances would not have adopted;
- **damage**: a certain harm, whether material, physical or moral;
- **a causal link** between the fault and the damage.

The victim must in principle prove all three elements ([ART:1353:CCIV]). The claim is time-barred after five years from the day the victim knew, or should have known, the facts enabling them to bring it ([ART:2224:CCIV]).

[VERIF:the limitation and evidence rules vary with the type of damage (physical injury, environmental harm...) and with any special liability regime that may apply — to be confirmed case by case]

[VERIF:the Court of Cassation's position on assessing causation where there are multiple causes]

*Prerecorded demo-mode answer, illustrating the agent's usual format (citation tagging, points to verify) — not a live analysis of your own situation.*"""

REPONSE_CHAT_PLAIDOIRIE_EN = """Here is the classic structure of a 10-minute civil pleading, with indicative timings:

1. **Opening (1 min)**: state the central question of the dispute in one sentence, and announce the plan.
2. **Statement of facts (2 min)**: keep only the facts that serve the argument, in chronological order, without premature legal characterisation.
3. **Argument (5 min)**: rank the grounds.
   - first the procedural grounds and inadmissibility objections, which prevent the merits from being examined ([ART:122:CPC]);
   - then the substantive grounds, from strongest to weakest, each followed by its evidence ([ART:9:CPC]).
4. **Rebuttal (1 min)**: answer the two or three most dangerous opposing arguments.
5. **Relief sought (1 min)**: restate precisely what is being asked of the court.

A methodological tip: only announce what you will genuinely prove, and keep your best argument for the end of the discussion.

[VERIF:the speaking time actually allotted depends on the court, the type of hearing and the presiding judge's practice — to be confirmed before the hearing]

For a full timed plan, with the arguments and exhibits of the case file, use **"Generate a pleading plan"** on the demonstration case "Diallo v. Atlas Logistique".

*Prerecorded demo-mode answer.*"""

_REPONSES_CHAT_PAR_LANGUE = {
    "fr": {
        "defaut": REPONSE_CHAT_DEFAUT_FR,
        "faute_grave": REPONSE_CHAT_FAUTE_GRAVE_FR,
        "delai": REPONSE_CHAT_DELAI_FR,
        "responsabilite": REPONSE_CHAT_RESPONSABILITE_FR,
        "plaidoirie": REPONSE_CHAT_PLAIDOIRIE_FR,
    },
    "en": {
        "defaut": REPONSE_CHAT_DEFAUT_EN,
        "faute_grave": REPONSE_CHAT_FAUTE_GRAVE_EN,
        "delai": REPONSE_CHAT_DELAI_EN,
        "responsabilite": REPONSE_CHAT_RESPONSABILITE_EN,
        "plaidoirie": REPONSE_CHAT_PLAIDOIRIE_EN,
    },
}

# Rétro-compatibilité : quelques modules/tests peuvent encore importer ces
# noms sans suffixe -- toujours la version française.
REPONSE_CHAT_DEFAUT = REPONSE_CHAT_DEFAUT_FR
REPONSE_CHAT_FAUTE_GRAVE = REPONSE_CHAT_FAUTE_GRAVE_FR
REPONSE_CHAT_DELAI = REPONSE_CHAT_DELAI_FR


def reponse_demo_pour_question(question: str) -> str:
    """Choisit la réponse préenregistrée selon des mots-clés simples (dans
    les deux langues -- un visiteur peut très bien garder une question en
    français avec une interface basculée en anglais, ou l'inverse), puis la
    renvoie dans la langue d'interface courante (analyse.langue_requete())."""
    q = question.lower()
    reponses = _REPONSES_CHAT_PAR_LANGUE.get(legacy_analyse.langue_requete(), _REPONSES_CHAT_PAR_LANGUE["fr"])
    if any(mot in q for mot in ("faute grave", "licenciement", "insubordination", "serious misconduct", "dismissal", "insubordination")):
        return reponses["faute_grave"]
    if any(mot in q for mot in ("délai", "delai", "prescription", "procédure", "procedure", "deadline", "statute of limitations")):
        return reponses["delai"]
    # Plaidoirie avant responsabilité : "plan de plaidoirie sur l'article
    # 1240" demande d'abord une structure, pas un cours sur l'article.
    if any(mot in q for mot in ("plaidoirie", "plaider", "pleading", "oral argument", "closing argument")):
        return reponses["plaidoirie"]
    if any(
        mot in q
        for mot in (
            "responsabilité", "responsabilite", "1240", "1241", "dommage", "préjudice", "prejudice",
            "délictuel", "delictuel", "liability", "damages",
        )
    ):
        return reponses["responsabilite"]
    return reponses["defaut"]
