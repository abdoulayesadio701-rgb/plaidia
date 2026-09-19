"""
demo_data_outils.py — Réponses du mode démo pour les fonctions qui n'avaient
pas de contenu préenregistré (analyse stylistique, traduction, extraction,
classement, cohérence, PV d'audience, réquisitoire, rapport d'instruction,
prise de note, note client, vérification procédurale, consultation de
jurisprudence, collecte de jurisprudence, chat contextuel). Sans elles, ces fonctions répondaient par une
erreur 503 sur le serveur public, donc inutilisables pour un visiteur.

Deux familles :
  - fonctions qui LISENT le texte saisi par des règles simples, sans aucun
    modèle (dates par expression régulière, mots-clés de nature, formules
    d'atténuation) : leur résultat dépend réellement de ce que le visiteur a
    collé ;
  - fonctions à contenu préenregistré (exemple fictif lié au dossier de
    démonstration, voir demo_data.py), identique quel que soit le texte saisi
    -- comme le plan ou le simulateur en mode démo.

Tout est produit au format exact des schémas Pydantic correspondants. Les
textes existent en FR et en EN, selon analyse.langue_requete().
"""

from __future__ import annotations

import re

import analyse as legacy_analyse


def _en() -> bool:
    return legacy_analyse.langue_requete() == "en"


def _choisir(fr, en):
    return en if _en() else fr


# --- Lecture simple du texte (aucun modèle) ---------------------------------

_MOIS = "janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre"
_MOIS_EN = "January|February|March|April|May|June|July|August|September|October|November|December"
_RE_DATE = re.compile(
    rf"\b(?:\d{{1,2}}(?:er)?\s+(?:{_MOIS})\s+\d{{4}}|\d{{1,2}}\s+(?:{_MOIS_EN})\s+\d{{4}}|\d{{1,2}}[/.-]\d{{1,2}}[/.-]\d{{2,4}})\b",
    re.IGNORECASE,
)
_RE_PARTIE = re.compile(r"\b(?:M\.|Mme|Mlle|Maître|Me|Mr\.?|Mrs\.?|Ms\.?|SAS|SARL|SA|Société|Company)\s+[A-ZÉÈ][\w'’-]+(?:\s+[A-ZÉÈ][\w'’-]+){0,3}")
_CODES = "civil|pénal|penal|du travail|de commerce|de procédure civile|de procédure pénale|de la consommation|de la sécurité sociale"
_RE_REFERENCE = re.compile(
    rf"\b(?:articles?|art\.)\s+[LRD]?\.?\s?\d[\d-]*(?:\s+(?:du|de la|des)\s+Code\s+(?:{_CODES}))?",
    re.IGNORECASE,
)


def _phrases(texte: str) -> list[str]:
    # Pas de coupure après une abréviation courante (« art. », « M. »...).
    coupure = r"(?<=[.!?;])(?<!\bart\.)(?<!\bM\.)(?<!\bMr\.)(?<!\bal\.)(?<!\bcf\.)\s+|\n+"
    return [p.strip() for p in re.split(coupure, texte) if len(p.strip()) > 15]


def _uniques(elements: list[str], maximum: int = 8) -> list[str]:
    vus: list[str] = []
    for e in elements:
        e = e.strip(" .,;:")
        if e and e.lower() not in (v.lower() for v in vus):
            vus.append(e)
    return vus[:maximum]


def _phrases_avec(texte: str, marqueurs: tuple[str, ...]) -> list[str]:
    return _uniques([p for p in _phrases(texte) if any(m in p.lower() for m in marqueurs)])


def _dates_du_texte(texte: str) -> list[str]:
    return _uniques(_RE_DATE.findall(texte))


def extraction_demo(texte: str) -> dict:
    return {
        "dates": _dates_du_texte(texte),
        "personnes_et_parties": _uniques(_RE_PARTIE.findall(texte)),
        "references": _uniques(_RE_REFERENCE.findall(texte)),
        "demandes": _phrases_avec(texte, ("demande", "sollicite", "prie ", "condamner", "requests", "seeks", "asks the")),
        "decisions": _phrases_avec(texte, ("condamne", "ordonne", "déboute", "deboute", "rejette", "dit que", "orders", "dismisses")),
    }


_NATURES = (
    ("assignation", ("assignation", "assigne", "assigné", "summons", "writ")),
    ("jugement", ("jugement", "par ces motifs", "judgment", "tribunal a rendu")),
    ("ordonnance", ("ordonnance", "le juge ordonne", "order of")),
    ("conclusions", ("conclusions", "plaise au tribunal", "submissions")),
    ("requête", ("requête", "requete", "petition", "application to")),
    ("citation", ("citation à comparaître", "citation a comparaitre", "citation directe")),
    ("procès-verbal", ("procès-verbal", "proces-verbal", "procès verbal", "minutes of", "l'an deux mille")),
    ("pièce", ("pièce n", "piece n", "bulletin de salaire", "contrat de travail", "exhibit")),
)


def classement_demo(texte: str) -> dict:
    bas = texte.lower()
    for nature, marqueurs in _NATURES:
        trouves = [m for m in marqueurs if m in bas]
        if trouves:
            return {
                "nature": nature,
                "justification": _choisir(
                    f"Le texte contient l'expression « {trouves[0]} », caractéristique de ce type de document (repérage par mots-clés en mode démo).",
                    f"The text contains the expression \"{trouves[0]}\", typical of this type of document (keyword matching in demo mode).",
                ),
                "confiance": "Moyenne",
            }
    return {
        "nature": "autre",
        "justification": _choisir(
            "Aucun mot-clé caractéristique n'a été repéré (mode démo : repérage par mots-clés, sans analyse du contenu).",
            "No characteristic keyword was found (demo mode: keyword matching, no content analysis).",
        ),
        "confiance": "Faible",
    }


def coherence_demo(documents: list[tuple[str, str]]) -> dict:
    """`documents` : [(nom, texte)]. Compare les dates de chaque document."""
    par_document = {nom: extraction_demo(texte) for nom, texte in documents}
    ensembles = [set(d.lower() for d in par_document[nom]["dates"]) for nom, _ in documents]
    communes = set.intersection(*ensembles) if ensembles else set()
    contradictions = []
    if len(documents) >= 2 and any(e - communes for e in ensembles):
        contradictions.append({
            "sujet": _choisir("Dates mentionnées", "Dates mentioned"),
            "document_1": ", ".join(sorted(ensembles[0] - communes)) or _choisir("aucune date propre à ce document", "no date specific to this document"),
            "document_2": ", ".join(sorted(ensembles[1] - communes)) or _choisir("aucune date propre à ce document", "no date specific to this document"),
            "gravite": "Moyenne",
        })
    coherents = [_choisir(f"Date présente dans les deux documents : {d}", f"Date found in both documents: {d}") for d in sorted(communes)]
    return {
        "elements_par_document": par_document,
        "contradictions": contradictions,
        "elements_coherents": coherents,
        "limites_analyse": _choisir(
            "Démonstration : seules les dates sont comparées, par repérage simple. Une vraie analyse compare aussi montants, noms et faits, et exige une clé API.",
            "Demo: only dates are compared, by simple matching. A real analysis also compares amounts, names and facts, and requires an API key.",
        ),
    }


def pv_audience_demo(notes: str) -> str:
    lignes = [ligne.strip(" -•\t") for ligne in notes.splitlines() if ligne.strip()]
    corps = "\n".join(f"- {ligne}" for ligne in lignes) or "- ..."
    return _choisir(
        "PROCÈS-VERBAL D'AUDIENCE (exemple généré en mode démo)\n\n"
        "Composition de la juridiction, parties et conseils : à compléter.\n\n"
        f"Déroulement de l'audience, d'après les notes consignées :\n{corps}\n\n"
        "Le présent procès-verbal, mis en forme automatiquement à titre d'illustration, doit être relu et complété par le greffier avant signature.",
        "HEARING MINUTES (example generated in demo mode)\n\n"
        "Composition of the court, parties and counsel: to be completed.\n\n"
        f"Course of the hearing, from the recorded notes:\n{corps}\n\n"
        "These minutes, formatted automatically for illustration, must be reviewed and completed by the clerk before signature.",
    )


def note_structuree_demo(note_brute: str) -> dict:
    phrases = _phrases(note_brute) or [note_brute.strip()]
    puces = "\n".join(f"- {p}" for p in phrases[:8])
    return {
        "note_structuree": _choisir(f"Note structurée (mode démo) :\n{puces}", f"Structured note (demo mode):\n{puces}"),
        "actions_a_faire": _phrases_avec(note_brute, ("à faire", "penser à", "relancer", "vérifier", "demander", "to do", "remember to", "follow up"))
        or [_choisir("Relire la note et préciser les prochaines étapes.", "Review the note and specify next steps.")],
        "points_a_retenir": phrases[:3],
    }


# --- Contenu préenregistré, lié au dossier de démonstration -----------------

_STYLE_EXEMPLE = {
    "fr": {
        "langage_de_couverture": [{"citation": "Il semblerait que le salarié ait, dans une certaine mesure, manqué à ses obligations.", "commentaire": "Deux atténuations successives : l'auteur ne s'engage pas pleinement sur la réalité du manquement."}],
        "affirmations_absolues": [{"citation": "Le salarié n'a jamais contesté ses retards.", "commentaire": "Formule catégorique : un seul écrit de contestation antérieur suffit à l'invalider."}],
        "voix_passive_suspecte": [{"citation": "Il a été convenu que le poste serait modifié.", "commentaire": "Ne dit pas qui a convenu de quoi ; l'accord du salarié n'est pas établi."}],
        "ruptures_registre": [{"citation": "Enfin, et au surplus, le comportement général du salarié était pour le moins critiquable.", "commentaire": "Changement de ton et d'argumentation : passage sans pièce à l'appui, signe d'un point moins maîtrisé."}],
        "synthese_strategique": "Exemple préenregistré (aucun marqueur n'a été repéré dans votre texte). Les atténuations et les formules absolues sont les angles d'attaque les plus rentables à l'audience.",
    },
    "en": {
        "langage_de_couverture": [{"citation": "It would seem that the employee, to a certain extent, failed in his obligations.", "commentaire": "Two successive hedges: the author does not fully commit to the reality of the breach."}],
        "affirmations_absolues": [{"citation": "The employee never contested his lateness.", "commentaire": "Categorical wording: a single earlier written objection is enough to defeat it."}],
        "voix_passive_suspecte": [{"citation": "It was agreed that the position would be changed.", "commentaire": "Does not say who agreed to what; the employee's consent is not established."}],
        "ruptures_registre": [{"citation": "Finally, and in addition, the employee's general conduct was questionable to say the least.", "commentaire": "Shift in tone and argument: an unsupported passage, a sign of a less controlled point."}],
        "synthese_strategique": "Pre-recorded example (no marker was found in your text). Hedges and absolute wording are the most profitable angles of attack at the hearing.",
    },
}

_COUVERTURE = ("il semblerait", "il semble que", "dans une certaine mesure", "en principe", "vraisemblablement", "it would seem", "to a certain extent", "arguably")
_ABSOLUS = ("jamais", "toujours", "en toute hypothèse", "sans aucun doute", "il est évident", "à l'évidence", "never", "always", "undoubtedly", "obviously")
_PASSIF = ("il a été convenu", "il apparaît que", "il a été", "il est apparu", "it was agreed", "it appears that")


def style_demo(texte: str) -> dict:
    trouves = {
        "langage_de_couverture": _phrases_avec(texte, _COUVERTURE),
        "affirmations_absolues": _phrases_avec(texte, _ABSOLUS),
        "voix_passive_suspecte": _phrases_avec(texte, _PASSIF),
    }
    if not any(trouves.values()):
        return _STYLE_EXEMPLE["en" if _en() else "fr"]
    commentaires = {
        "langage_de_couverture": _choisir("Atténuation : l'auteur ne s'engage pas pleinement.", "Hedge: the author does not fully commit."),
        "affirmations_absolues": _choisir("Formule catégorique : une seule exception suffit à l'invalider.", "Categorical wording: a single exception is enough to defeat it."),
        "voix_passive_suspecte": _choisir("Forme impersonnelle : n'indique pas qui a fait quoi.", "Impersonal form: does not say who did what."),
    }
    sortie = {cle: [{"citation": c, "commentaire": commentaires[cle]} for c in valeurs] for cle, valeurs in trouves.items()}
    sortie["ruptures_registre"] = []
    sortie["synthese_strategique"] = _choisir(
        "Repérage par formules types (mode démo). Ces passages sont les premiers angles d'attaque à examiner ; une analyse complète exige une clé API.",
        "Detection by typical wording (demo mode). These passages are the first angles of attack to examine; a full analysis requires an API key.",
    )
    return sortie


_TRADUCTIONS = {
    "fr_vers_en": (
        "English",
        "[Demo: translation of a sample excerpt, independent of the text entered.]\n\n"
        "The employee challenges his dismissal for serious misconduct. He argues that the three instances of lateness "
        "coincided with a rail strike and that he had no disciplinary record in five years of service.",
    ),
    "en_vers_fr": (
        "Français",
        "[Démonstration : traduction d'un extrait type, indépendante du texte saisi.]\n\n"
        "Le salarié conteste son licenciement pour faute grave. Il soutient que les trois retards coïncidaient avec une "
        "grève des transports et qu'il n'avait aucun antécédent disciplinaire en cinq ans d'ancienneté.",
    ),
}
_MOTS_EN = re.compile(r"\b(the|and|of|to|is|was|his|her|with|that|for)\b", re.IGNORECASE)
_MOTS_FR = re.compile(r"\b(le|la|les|des|et|est|une|un|du|que|pour|dans)\b", re.IGNORECASE)


def traduction_demo(texte: str) -> dict:
    anglais = len(_MOTS_EN.findall(texte)) > len(_MOTS_FR.findall(texte))
    cible, traduit = _TRADUCTIONS["en_vers_fr" if anglais else "fr_vers_en"]
    return {"langue_detectee": "English" if anglais else "Français", "langue_cible": cible, "texte_traduit": traduit}


def verification_procedurale_demo() -> dict:
    return _choisir(
        {
            "echeances_identifiees": [
                {"echeance": "Contestation du licenciement devant le conseil de prud'hommes (12 mois à compter de la notification) [ART:L.1471-1:CTRAV]", "date": "28 février 2025", "statut": "Possiblement dépassée"},
                {"echeance": "Délai d'appel d'un éventuel jugement (1 mois à compter de la notification)", "date": "non précisée", "statut": "Date incertaine"},
            ],
            "actes_potentiellement_manquants": [
                "Justificatif de la remise en main propre de la convocation à l'entretien préalable.",
                "Compte rendu de l'entretien préalable du 21 février 2024 par le conseiller du salarié.",
            ],
            "points_attention": [
                "Vérifier le respect du délai entre l'entretien préalable et la notification du licenciement.",
                "La date de réception de la lettre de licenciement n'est pas établie : elle fait courir le délai de contestation.",
            ],
        },
        {
            "echeances_identifiees": [
                {"echeance": "Challenge to the dismissal before the labour tribunal (12 months from notification) [ART:L.1471-1:CTRAV]", "date": "28 February 2025", "statut": "Possiblement dépassée"},
                {"echeance": "Time limit to appeal any judgment (1 month from notification)", "date": "non précisée", "statut": "Date incertaine"},
            ],
            "actes_potentiellement_manquants": [
                "Proof of hand delivery of the summons to the preliminary meeting.",
                "Report of the 21 February 2024 preliminary meeting by the employee's adviser.",
            ],
            "points_attention": [
                "Check compliance with the time between the preliminary meeting and the dismissal notification.",
                "The date the dismissal letter was received is not established: it starts the time limit to challenge it.",
            ],
        },
    )


def note_client_demo() -> str:
    return _choisir(
        "Madame, Monsieur,\n\n"
        "Voici où en est votre dossier, en langage simple.\n\n"
        "Ce qui se passe : votre employeur vous a licencié pour « faute grave », en invoquant trois retards et un désaccord avec votre chef d'équipe. "
        "Vous contestez ces reproches devant le conseil de prud'hommes de Bobigny.\n\n"
        "Ce que nous défendons : vos cinq années sans aucun avertissement, et le fait que les retards coïncident avec une grève des transports.\n\n"
        "Les prochaines étapes : rassembler les pièces qui manquent, préparer l'audience, puis plaider. Nous vous tiendrons informé à chaque étape.\n\n"
        "[Exemple préenregistré en mode démo, sur un dossier fictif.]",
        "Dear Sir or Madam,\n\n"
        "Here is where your case stands, in plain language.\n\n"
        "What is happening: your employer dismissed you for \"serious misconduct\", citing three instances of lateness and a disagreement with your team leader. "
        "You are challenging these allegations before the labour tribunal of Bobigny.\n\n"
        "What we are arguing: your five years without any warning, and the fact that the lateness coincided with a transport strike.\n\n"
        "Next steps: gather the missing documents, prepare the hearing, then plead. We will keep you informed at each stage.\n\n"
        "[Pre-recorded example in demo mode, on a fictional case.]",
    )


def consultation_jurisprudence_demo() -> dict:
    return _choisir(
        {
            "notions": {
                "domaine": "Droit du travail",
                "qualification_juridique": "Licenciement pour faute grave : retards répétés et insubordination alléguée",
                "mots_cles_recherche": ["faute grave", "retards répétés", "grève des transports", "insubordination"],
                "but": "",
            },
            "reponse": (
                "Exemple préenregistré (mode démo).\n\n"
                "La faute grave suppose un manquement rendant impossible le maintien du salarié dans l'entreprise pendant le préavis "
                "[ART:L.1234-1:CTRAV]. Des retards isolés, sans avertissement préalable et liés à un événement extérieur, sont en principe "
                "insuffisants. [VERIF:décisions récentes de la Cour de cassation sur des retards liés à une grève des transports]\n\n"
                "Aucune décision précise n'est citée ici : une vraie consultation interroge Légifrance et exige une clé API."
            ),
            "verification": None,
        },
        {
            "notions": {
                "domaine": "Employment law",
                "qualification_juridique": "Dismissal for serious misconduct: repeated lateness and alleged insubordination",
                "mots_cles_recherche": ["serious misconduct", "repeated lateness", "transport strike", "insubordination"],
                "but": "",
            },
            "reponse": (
                "Pre-recorded example (demo mode).\n\n"
                "Serious misconduct requires a breach making it impossible to keep the employee in the company during the notice period "
                "[ART:L.1234-1:CTRAV]. Isolated lateness, without prior warning and linked to an external event, is in principle "
                "insufficient. [VERIF:recent Court of Cassation decisions on lateness linked to a transport strike]\n\n"
                "No specific decision is cited here: a real consultation queries Légifrance and requires an API key."
            ),
            "verification": None,
        },
    )


def requisitoire_demo() -> dict:
    return _choisir(
        {
            "qualification_retenue": "Vol en réunion (exemple fictif)",
            "faits_et_elements_invoques": ["Images de vidéosurveillance montrant les deux prévenus.", "Aveux partiels recueillis en garde à vue."],
            "circonstances_aggravantes": ["Réunion de plusieurs auteurs."],
            "circonstances_attenuantes": ["Absence d'antécédent judiciaire.", "Indemnisation de la victime."],
            "peine_requise": "12 mois d'emprisonnement dont 6 avec sursis (exemple fictif)",
            "points_attention": ["Vérifier la régularité de la garde à vue avant d'invoquer les aveux.", "La qualification de « réunion » suppose de caractériser la participation de chacun."],
        },
        {
            "qualification_retenue": "Theft by several perpetrators (fictional example)",
            "faits_et_elements_invoques": ["CCTV footage showing both defendants.", "Partial confessions obtained in police custody."],
            "circonstances_aggravantes": ["Several perpetrators acting together."],
            "circonstances_attenuantes": ["No prior criminal record.", "Victim compensated."],
            "peine_requise": "12 months' imprisonment, 6 of them suspended (fictional example)",
            "points_attention": ["Check the lawfulness of the police custody before relying on the confessions.", "The \"several perpetrators\" qualification requires showing each person's participation."],
        },
    )


def rapport_instruction_demo() -> dict:
    return _choisir(
        {
            "actes_instruction": ["Audition du plaignant.", "Audition de deux témoins.", "Perquisition au domicile du mis en examen."],
            "elements_a_charge": ["Concordance de deux témoignages.", "Objet retrouvé lors de la perquisition."],
            "elements_a_decharge": ["Alibi allégué, non encore vérifié.", "Absence d'empreintes exploitables."],
            "mesures_ordonnees": ["Expertise informatique.", "Vérification de l'alibi par réquisition téléphonique."],
            "sens_propose": "Poursuite de l'information, dans l'attente des expertises (exemple fictif)",
            "points_attention": ["Deux mesures restent en cours : le sens proposé est provisoire."],
        },
        {
            "actes_instruction": ["Hearing of the complainant.", "Hearing of two witnesses.", "Search of the suspect's home."],
            "elements_a_charge": ["Two consistent witness statements.", "Item found during the search."],
            "elements_a_decharge": ["Alleged alibi, not yet verified.", "No usable fingerprints."],
            "mesures_ordonnees": ["Computer expert report.", "Alibi check by telephone records request."],
            "sens_propose": "Continue the investigation pending the expert reports (fictional example)",
            "points_attention": ["Two measures are still pending: the proposed outcome is provisional."],
        },
    )


def chat_contextuel_demo() -> str:
    return _choisir(
        "Mode démo : l'assistant ne peut pas modifier ce résultat sans clé API. Vous pouvez tout de même copier, exporter ou supprimer le résultat affiché, ou renseigner votre propre clé Anthropic dans les paramètres pour activer les modifications.",
        "Demo mode: the assistant cannot edit this result without an API key. You can still copy, export or delete the displayed result, or enter your own Anthropic key in the settings to enable edits.",
    )


def decisions_collectees_demo(domaine: str) -> list[dict]:
    """Décisions FICTIVES pour la collecte de jurisprudence en mode démo : aucun
    appel à Judilibre, et aucune vraie décision inventée -- chaque référence
    porte la mention « fictive »."""
    domaine = domaine or _choisir("Droit du travail", "Employment law")
    source = _choisir("Judilibre (démonstration)", "Judilibre (demo)")
    return _choisir(
        [
            {"reference": "Cass. soc., 1 janvier 2024, n° 00-00.001 (décision fictive de démonstration)",
             "resume": "Des retards isolés, sans avertissement préalable, ne caractérisent pas à eux seuls une faute grave.", "domaine": domaine, "source": source},
            {"reference": "Cass. soc., 1 février 2024, n° 00-00.002 (décision fictive de démonstration)",
             "resume": "Le juge apprécie la faute grave au regard de l'ancienneté du salarié et de l'absence d'antécédent disciplinaire.", "domaine": domaine, "source": source},
            {"reference": "Cass. soc., 1 mars 2024, n° 00-00.003 (décision fictive de démonstration)",
             "resume": "La preuve d'une insubordination ne peut reposer sur le seul témoignage du supérieur hiérarchique concerné.", "domaine": domaine, "source": source},
        ],
        [
            {"reference": "Cass. soc., 1 January 2024, no. 00-00.001 (fictional demo decision)",
             "resume": "Isolated lateness, without prior warning, does not on its own amount to serious misconduct.", "domaine": domaine, "source": source},
            {"reference": "Cass. soc., 1 February 2024, no. 00-00.002 (fictional demo decision)",
             "resume": "The court assesses serious misconduct in light of the employee's tenure and lack of disciplinary record.", "domaine": domaine, "source": source},
            {"reference": "Cass. soc., 1 March 2024, no. 00-00.003 (fictional demo decision)",
             "resume": "Proof of insubordination cannot rest solely on the testimony of the superior concerned.", "domaine": domaine, "source": source},
        ],
    )


# --- Barre de commande (interprétation d'intention) -------------------------
# Ordre significatif : les formulations les plus spécifiques d'abord (« note
# client » avant « note », « vérification procédurale » avant « procédure »...).
_INTENTIONS = (
    ("note_client", ("note client", "note pour le client", "client note")),
    ("notes_consulter", ("consulter les notes", "mes notes", "voir les notes", "view notes", "my notes")),
    ("verification", ("vérification", "verification", "vérifier la procédure", "check the procedure")),
    ("delais", ("délai", "delai", "échéance", "echeance", "deadline")),
    ("entrainement", ("entraîn", "entrain", "répét", "repet", "chronomét", "practi", "rehears")),
    ("bordereau", ("bordereau", "exhibit list", "liste des pièces")),
    ("chronologie", ("chronolog", "timeline")),
    ("simulateur", ("objection", "simul")),
    ("plan", ("plan", "plaidoirie", "plea")),
    ("rapport", ("rapport", "report")),
    ("resumer", ("résum", "resum", "summar")),
    ("analyser", ("conclusion", "analys", "adverse")),
    ("note", ("note",)),
    ("importer", ("import", "ajouter des documents", "add documents", "upload")),
)
_LIBELLES_INTENTION = {
    "note_client": ("rédiger une note client", "write a client note"),
    "notes_consulter": ("consulter les notes", "view the notes"),
    "verification": ("vérifier la procédure", "check the procedure"),
    "delais": ("suivre les délais de procédure", "track procedural deadlines"),
    "entrainement": ("s'entraîner à plaider", "practise your plea"),
    "bordereau": ("tenir le bordereau de pièces", "manage the exhibit list"),
    "chronologie": ("construire la chronologie", "build the timeline"),
    "simulateur": ("simuler les objections", "simulate objections"),
    "plan": ("générer un plan de plaidoirie", "generate a plea plan"),
    "rapport": ("générer le rapport complet", "generate the full report"),
    "resumer": ("résumer le dossier", "summarise the case"),
    "analyser": ("analyser des conclusions adverses", "analyse opposing submissions"),
    "note": ("prendre une note", "take a note"),
    "importer": ("importer des documents", "import documents"),
}
_RE_DUREE = re.compile(r"(\d{1,3})\s*(?:min\b|minutes?\b|mn\b)", re.IGNORECASE)


def intention_demo(texte: str) -> dict:
    """Interprétation par mots-clés (sans modèle) de la barre de commande, pour
    que l'exemple affiché (« établir un plan de 10 minutes ») fonctionne aussi
    en mode démo. Aucune correspondance : « menu » avec confiance basse, que
    la barre de commande traduit par une orientation vers la navigation."""
    bas = texte.lower()
    for action, marqueurs in _INTENTIONS:
        if any(m in bas for m in marqueurs):
            duree = None
            if action in ("plan", "entrainement"):
                correspondance = _RE_DUREE.search(bas)
                duree = int(correspondance.group(1)) if correspondance else None
            libelle = _choisir(*_LIBELLES_INTENTION[action])
            return {
                "action": action,
                "duree_minutes": duree,
                "confiance": "haute",
                "reformulation": _choisir(f"Compris : {libelle}.", f"Understood: {libelle}."),
            }
    return {"action": "menu", "duree_minutes": None, "confiance": "basse", "reformulation": ""}
