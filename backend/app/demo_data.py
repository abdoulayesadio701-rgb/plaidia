"""
demo_data.py — Contenu préenregistré du mode démo (voir demo.py) : un
dossier fictif de droit du travail ("Diallo c/ Atlas Logistique") avec son
analyse de conclusions adverses, son plan de plaidoirie, son simulateur
d'objections et sa chronologie -- au format exact des schémas Pydantic
correspondants, pour que le front n'ait strictement rien à distinguer entre
une réponse démo et une réponse réelle.

Toute ressemblance avec une affaire réelle est fortuite : noms, dates et
pièces sont inventés pour l'exercice.
"""

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

CONCLUSIONS_DEMO = {
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

PLAN_DEMO = {
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

SIMULATEUR_DEMO = {
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

CHRONOLOGIE_DEMO = {
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

RESUME_DEMO = {
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

# --- Chat : quelques réponses préenregistrées selon des mots-clés simples,
# et une réponse générique par défaut qui oriente vers les actions cannées
# ci-dessus. Chacune conserve une balise [VERIF:...] (ou [ART:...]) pour
# démontrer le balisage anti-hallucination même en mode démo -- voir
# analyse.REGLE_BALISAGE_CITATIONS.

REPONSE_CHAT_DEFAUT = """Vous êtes en **mode démo** de Plaid'IA : aucune clé API n'est configurée sur ce serveur public, je ne peux donc pas traiter librement une question ici.

Ce que vous pouvez explorer dès maintenant, avec des données réalistes préenregistrées sur le dossier de démonstration « Diallo c/ Atlas Logistique » :
- **Analyser des conclusions adverses**
- **Générer un plan de plaidoirie** chronométré
- **Simuler les objections** probables du magistrat ou de la partie adverse
- **Construire sa chronologie** automatique

Pour poser une vraie question et obtenir une réponse générée en direct, utilisez **« Utiliser ma propre clé Anthropic »** en pied de page — votre clé reste dans votre navigateur et n'est jamais journalisée par le serveur.

[VERIF:comme toute réponse de Plaid'IA, même hors mode démo, ceci resterait à vérifier avant tout usage professionnel — c'est tout l'esprit de ce garde-fou]."""

REPONSE_CHAT_FAUTE_GRAVE = """Dans le dossier de démonstration (Diallo c/ Atlas Logistique), la qualification de faute grave retenue par l'employeur repose sur des retards répétés et un incident d'insubordination.

En droit du travail français, la faute grave est celle qui rend impossible le maintien du salarié dans l'entreprise, même pendant la durée du préavis : elle prive le salarié de son préavis et de son indemnité de licenciement.

Deux éléments fragilisent cette qualification dans les faits présentés ici :
- l'absence de tout antécédent disciplinaire en cinq ans d'ancienneté ;
- la coïncidence des retards avec un mouvement de grève des transports en commun.

[VERIF:la position de la jurisprudence de la chambre sociale sur la prise en compte des perturbations de transport dans l'appréciation de la faute grave]

*Réponse préenregistrée du mode démo, illustrant le format habituel de l'agent — pas une analyse en direct de votre situation.*"""

REPONSE_CHAT_DELAI = """Sur le plan procédural, une contestation de licenciement devant le conseil de prud'hommes doit en principe être introduite dans un délai de 12 mois à compter de la notification du licenciement ([ART:L.1471-1:CTRAV]).

[VERIF:ce délai peut varier selon la nature exacte du grief invoqué (discrimination, harcèlement...) — à confirmer au cas par cas]

Dans le dossier de démonstration, le licenciement a été notifié le 28 février 2024 et la saisine du conseil de prud'hommes est intervenue le 15 avril 2024 — largement dans les délais.

*Réponse préenregistrée du mode démo.*"""


def reponse_demo_pour_question(question: str) -> str:
    q = question.lower()
    if any(mot in q for mot in ("faute grave", "licenciement", "insubordination")):
        return REPONSE_CHAT_FAUTE_GRAVE
    if any(mot in q for mot in ("délai", "delai", "prescription", "procédure", "procedure")):
        return REPONSE_CHAT_DELAI
    return REPONSE_CHAT_DEFAUT
