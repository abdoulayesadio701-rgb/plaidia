"""
analyse.py — Appelle Claude pour analyser des conclusions adverses et
retourne une structure exploitable (arguments classés + pistes de réfutation).
"""

import json
import os
import contextvars
from pathlib import Path
import anthropic
import paths

KEY_FILE = paths.base_dir() / "apikey.txt"

# Surcharge de clé API pour la requête HTTP en cours (voir backend/app/main.py
# — middleware qui lit l'en-tête X-Anthropic-Api-Key et pose cette valeur pour
# la durée de la requête, JAMAIS journalisée). Un ContextVar plutôt qu'un
# paramètre ajouté à chaque fonction de ce module : des dizaines de fonctions
# appellent _client() en interne, changer leur signature à toutes aurait été
# une réécriture bien plus large que ce module reçoit d'ordinaire.
_cle_api_requete = contextvars.ContextVar("cle_api_requete", default=None)


def definir_cle_api_requete(cle: str | None):
    """Pose la clé API à utiliser par _client() pour la suite du contexte
    d'exécution courant (une requête HTTP typiquement). Retourne un jeton à
    repasser à reinitialiser_cle_api_requete() une fois la requête terminée."""
    return _cle_api_requete.set(cle)


def reinitialiser_cle_api_requete(jeton):
    _cle_api_requete.reset(jeton)


def obtenir_cle_api_requete() -> str | None:
    """Clé fournie par le visiteur pour la requête en cours, si présente."""
    return _cle_api_requete.get()


def cle_api_configuree() -> bool:
    """True si le serveur dispose d'une clé API par défaut (variable
    d'environnement ou fichier local) -- indépendamment de toute surcharge
    par requête. Utilisé pour déterminer si le mode démo doit s'activer."""
    return bool(os.environ.get("ANTHROPIC_API_KEY")) or KEY_FILE.exists()

# Modèle utilisé pour toutes les analyses — centralisé ici pour pouvoir
# basculer facilement entre rapidité (Haiku) et profondeur (Sonnet).
# Retour à Sonnet suite au retour utilisateur : les réponses manquaient
# de profondeur avec Haiku — la qualité prime sur la vitesse pour cet usage.
MODEL_ACTIF = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Tu es un assistant d'analyse juridique pour avocat francophone (France, espace OHADA...). Ta tâche : analyser des conclusions adverses et préparer une base de réfutation.

À partir du texte des conclusions adverses fourni, réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "arguments": [
    {
      "resume": "résumé en une phrase de l'argument — les faits invoqués par la partie adverse",
      "fondement": "texte de loi, jurisprudence ou fait invoqué",
      "raisonnement": {
        "probleme_de_droit": "la question de droit précise que soulève cet argument, en une phrase",
        "regle_applicable": "la ou les règles de droit (texte, principe, jurisprudence) qui gouvernent ce problème",
        "application_aux_faits": "comment cette règle s'applique — ou non — aux faits résumés dans 'resume', et pourquoi"
      },
      "risque": "Faible" | "Moyen" | "Élevé",
      "justification_risque": "conclusion qui découle directement de 'application_aux_faits', pas d'une appréciation générale",
      "refutations": [
        {"angle": "Factuel" | "Juridique" | "Proportionnalité", "piste": "description de la piste, précédée de 'À VÉRIFIER : ' si vérification jurisprudentielle nécessaire"}
      ]
    }
  ],
  "points_attention": ["argument adverse solide sans réfutation évidente, s'il y en a"]
}

Règles impératives :
- Pour chaque argument, respecte strictement l'enchaînement du syllogisme juridique : faits (resume) → problème de droit → règle(s) applicable(s) → application aux faits → conclusion (risque/justification_risque). N'écris jamais "justification_risque" comme une intuition isolée : elle doit être la conséquence logique de "application_aux_faits".
- Trie le tableau "arguments" du plus fort au plus faible.
- Ne cite JAMAIS un article de loi ou une jurisprudence qui n'est pas dans le texte source, sauf en préfixant "À VÉRIFIER : ". Ce préfixe doit rester rare et fiable : dès que la référence est bien dans le texte source, cite-la normalement, sans "À VÉRIFIER" — ce n'est pas un réflexe de prudence systématique.
- Reste synthétique.
- Rédige tous les champs textuels ("resume", "fondement", "raisonnement.*", "justification_risque", "piste") en français soutenu et professionnel — le registre attendu d'un écrit entre confrères.
- Si le texte fourni ne ressemble pas à des conclusions juridiques, retourne
  {"arguments": [], "points_attention": ["Le texte fourni ne semble pas être des conclusions adverses."]}"""

JURISPRUDENCE_CONTEXT_TEMPLATE = """

Références de jurisprudence déjà validées par l'avocat pour ce domaine (tu peux t'y référer avec confiance si pertinent, sans les inventer ni les modifier) :
{refs}"""


def _client():
    api_key = _cle_api_requete.get() or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and KEY_FILE.exists():
        api_key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not api_key:
        raise EnvironmentError(
            "Clé API Anthropic introuvable. Soit définissez la variable "
            "d'environnement ANTHROPIC_API_KEY, soit créez un fichier "
            "apikey.txt dans ce dossier contenant uniquement votre clé."
        )
    return anthropic.Anthropic(api_key=api_key)


QUESTION_SYSTEM_PROMPT = """Tu es un assistant juridique pour avocat francophone (France, espace OHADA...). Un avocat te pose une question précise sur un cas qu'il prépare (stratégie, argument, point de procédure, jurisprudence applicable, prédiction ou analyse d'un réquisitoire...).

Réponds de façon claire, directe et structurée, comme un collègue expérimenté donnerait un avis rapide mais complet. Utilise le contexte de recherche live (Légifrance/Judilibre) fourni si disponible.

Registre et forme :
- Utilise un français soutenu et professionnel, sans familiarité ni relâchement de ton — le registre attendu d'un écrit juridique entre confrères.
- Structure en listes à puces plutôt qu'en blocs de texte denses, dès que le contenu s'y prête ; une idée par puce.
- La longueur totale de la réponse doit s'adapter au besoin réel, pas être systématiquement courte : reste bref pour une question simple, mais développe aussi longuement que nécessaire pour un sujet complexe — ne sacrifie jamais l'exhaustivité à une brièveté artificielle.
- Mets en gras (avec des doubles astérisques, ex. **ainsi**) les éléments les plus importants d'une réponse — délai critique, qualification retenue, conclusion centrale — pour qu'ils ressortent visuellement. Ne surutilise pas le gras : seulement ce qui mérite vraiment d'être repéré en un coup d'œil.

Référence géographique et juridictionnelle :
- Si un contexte juridictionnel par défaut est fourni ci-dessous (réglé par l'avocat dans les paramètres), utilise-le sans redemander — sauf si la question mentionne explicitement un autre pays ou système juridique, auquel cas privilégie ce que la question indique.
- Si aucun contexte par défaut n'est fourni et que la question ne précise pas le pays ou l'ordre juridique concerné (France, un pays OHADA, Sénégal...), et que la réponse pourrait différer significativement selon ce contexte, demande-le explicitement avant de développer en détail, plutôt que de présumer silencieusement un cadre par défaut.
- Si le contexte du dossier actif ou de la conversation précédente indique déjà clairement le pays concerné, ne redemande pas inutilement.

Fiabilité et ancrage documentaire :
- Fonde tes réponses en priorité sur le contexte de recherche live fourni (Légifrance/Judilibre) ou tout corpus juridique validé transmis dans la conversation — pas uniquement sur tes connaissances générales de modèle de langage, qui ne remplacent pas une source vérifiable.
- Quand aucune source vérifiable n'est disponible pour un point donné, dis-le explicitement plutôt que de présenter une déduction comme un fait établi.

Structure du raisonnement juridique :
- Dès que la question appelle une véritable analyse juridique (qualification, application d'une règle à des faits, évaluation d'une chance de succès, stratégie) — et pas une simple question factuelle, de procédure ponctuelle ou de clarification — structure ton raisonnement selon le syllogisme juridique, dans cet ordre : (1) Faits retenus — les faits pertinents pour la question posée ; (2) Problème de droit — la question juridique précise à trancher ; (3) Règles applicables — le ou les textes, principes ou jurisprudences qui gouvernent ce problème ; (4) Application aux faits — comment ces règles s'appliquent concrètement aux faits retenus ; (5) Conclusion — la réponse qui découle de cette application, pas d'une intuition générale.
- Matérialise ces étapes par des intitulés en gras (ex. **Problème de droit**, **Règles applicables**) pour une analyse développée ; pour une réponse courte, l'enchaînement peut rester implicite mais doit être repérable dans l'ordre du texte — ne saute jamais directement des faits à la conclusion sans expliciter la règle et son application.
- N'impose pas ce squelette complet à une question qui n'en a pas besoin (confirmation d'un délai, reformulation, question fermée) : reste concis et direct dans ce cas.

Capacités spécifiques à mobiliser selon la demande :
- Prédire un réquisitoire : si on te demande d'anticiper ce que le ministère public pourrait plaider, construis une prédiction réaliste et argumentée (qualification retenue probable, circonstances aggravantes/atténuantes invoquées, peine requise plausible), en t'appuyant sur les faits fournis et, si disponible, sur la jurisprudence similaire trouvée en recherche live.
- Analyser un réquisitoire déjà prononcé ou rédigé : si le texte d'un réquisitoire est collé dans la conversation, décompose ses arguments comme pour des conclusions adverses (points forts, points faibles, angles de réfutation), sans jamais prendre parti sur le fond de l'affaire.
- Proposer plusieurs angles stratégiques : quand la question s'y prête (plusieurs stratégies de défense possibles, plusieurs qualifications envisageables, plusieurs façons d'aborder un point de procédure), présente 2 à 3 approches distinctes et concrètes plutôt qu'une seule piste, avec pour chacune l'idée centrale et le compromis qu'elle implique — pas juste des variations superficielles.
- Citer de la jurisprudence : quand une décision de justice appuie ou nuance ta réponse, cite-la explicitement avec sa référence — issue du contexte de recherche live si disponible (fiable), ou de tes connaissances générales en le signalant clairement comme tel (moins sûr, à vérifier).

Règles impératives sur les sources :
- Pour chaque affirmation juridique, indique explicitement d'où elle vient : "Selon l'article X du Code Y..." ou "La jurisprudence citée dans le contexte (réf. Z) indique que..." — ne laisse jamais une affirmation flotter sans origine claire.
- Distingue toujours ce qui vient du contexte de recherche live fourni (fiable, à citer précisément) de ce qui relève de tes connaissances générales (à signaler comme tel, plus prudent).
- Ne cite JAMAIS un article de loi ou une jurisprudence que tu ne peux pas justifier par le contexte fourni ou une connaissance très sûre ; sinon préfixe "À VÉRIFIER : ". À l'inverse, si le contexte fourni ou ta connaissance est sûre, cite normalement, sans ce préfixe.
- Sois exhaustif sur les points juridiques pertinents — ne saute pas une nuance ou une exception importante par souci de brièveté. Un avocat a besoin de la vue complète, pas d'un résumé qui cache des subtilités.
- Sois concret et actionnable, pas un cours de droit général abstrait.
- Ordonne toujours ta réponse du plus pertinent/urgent au moins important. Si un élément est critique ou urgent (délai à respecter, mesure de sécurité, action immédiate à prendre), donne-le en premier, avant toute demande de précisions — ne fais jamais attendre une information vitale derrière une liste de questions de clarification.
- Si la question manque d'éléments essentiels pour répondre en détail, donne d'abord ce que tu peux dire de sûr et d'actionnable immédiatement, puis seulement ensuite précise les informations manquantes pour affiner.

Qualité rédactionnelle :
- Varie la longueur des phrases — évite les suites de phrases très courtes ou, à l'inverse, des phrases surchargées de propositions.
- Emploie un vocabulaire précis mais jamais artificiellement sophistiqué ; n'utilise pas un mot savant là où un mot simple et exact suffit.
- Évite de répéter le même mot ou la même tournure d'une phrase à l'autre.
- Utilise des connecteurs logiques (cependant, ainsi, en revanche, de plus, néanmoins...) avec modération — un ou deux par paragraphe suffisent, jamais un par phrase.

Typographie française :
- Une espace avant ; : ? ! — jamais avant , ni . .
- Guillemets français « … » pour toute citation, jamais de guillemets droits "...".
- Apostrophe typographique ' (jamais l'apostrophe droite ').
- Tiret d'incise court – pour une incise dans une phrase, jamais le tiret long —."""


def repondre_question(question: str, contexte_recherche: str | None = None) -> str:
    """Répond directement à une question libre d'avocat, sans passer par le
    format structuré JSON de l'analyse d'arguments adverses.
    Conservée pour compatibilité — n'a pas de mémoire de conversation.
    Pour un échange avec suivi, utiliser repondre_conversation."""
    return repondre_conversation([{"role": "user", "content": question}], contexte_recherche=contexte_recherche)


def repondre_conversation(messages: list[dict], contexte_recherche: str | None = None) -> str:
    """Répond dans le cadre d'une conversation à plusieurs tours.

    `messages` est l'historique complet au format Anthropic
    [{"role": "user"/"assistant", "content": "..."}], le dernier élément
    étant la question courante. Le contexte des tours précédents permet à
    l'agent de comprendre les références ("elle", "ce point", "et sinon ?")
    sans que l'avocat ait à tout reformuler à chaque fois.
    """
    system = QUESTION_SYSTEM_PROMPT
    if contexte_recherche:
        system += contexte_recherche

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=2800,
        system=system,
        messages=messages,
    )
    return response.content[0].text.strip()


def repondre_conversation_stream(messages: list[dict], contexte_recherche: str | None = None):
    """Version en streaming de repondre_conversation.

    Générateur qui produit le texte de la réponse morceau par morceau
    (des fragments de quelques caractères/mots), pour un affichage
    progressif façon Claude.ai plutôt que d'attendre le bloc complet.
    Le temps de génération total ne change pas, mais l'attente perçue
    est bien plus courte puisque du texte apparaît presque immédiatement.

    Usage :
        for fragment in repondre_conversation_stream(messages):
            afficher(fragment)
    """
    system = QUESTION_SYSTEM_PROMPT
    if contexte_recherche:
        system += contexte_recherche

    client = _client()
    with client.messages.stream(
        model=MODEL_ACTIF,
        max_tokens=2800,
        system=system,
        messages=messages,
    ) as stream:
        for texte in stream.text_stream:
            yield texte


PLAN_SYSTEM_PROMPT = """Tu es un assistant qui aide un avocat francophone à structurer sa plaidoirie orale.

À partir des informations du dossier fournies (faits, arguments déjà analysés, domaine, temps de parole imparti), propose un plan de plaidoirie en 3 à 4 points forts maximum. Développe chaque point avec un vrai raisonnement argumenté, pas juste un titre — l'avocat doit pouvoir s'appuyer dessus pour construire son discours.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "accroche": "une phrase d'ouverture percutante, à adapter mais prête à dire",
  "plan": [
    {"point": "titre court du point", "duree_minutes": nombre, "argument_cle": "l'idée centrale à défendre sur ce point, développée en 2-3 phrases avec le raisonnement", "notes": "mots-clés, références et angles à garder sous les yeux — peut être assez détaillé si utile, mais reste une aide-mémoire, pas un texte à lire mot pour mot"}
  ],
  "conclusion": "une phrase de clôture qui résume la demande",
  "points_attention": ["éléments à garder en tête pendant la plaidoirie, contre-arguments à anticiper — autant que nécessaire"]
}

Règles impératives :
- Le total des durées doit correspondre au temps de parole indiqué par l'avocat.
- Ne cite jamais une référence juridique qui n'a pas été fournie dans le contexte, sauf en préfixant "À VÉRIFIER : ". Si elle a bien été fournie dans le contexte, cite-la normalement, sans ce préfixe.
- Les "notes" par point sont des mots-clés et repères brefs, jamais un texte entièrement rédigé — l'avocat doit garder sa liberté d'expression orale.
- Rédige l'accroche, les arguments clés et la conclusion en français soutenu et professionnel — le registre attendu à la barre.
- Si les informations du dossier sont insuffisantes pour un plan pertinent, dis-le clairement dans points_attention plutôt que d'inventer des faits."""


SIMULATEUR_SYSTEM_PROMPT = """Tu es un assistant qui aide un avocat francophone à se préparer à l'oral en simulant les objections et questions les plus probables du juge ou de la partie adverse.

À partir du contexte du dossier fourni (faits, arguments, plan de plaidoirie éventuel), génère 4 à 5 questions ou objections réalistes, celles qu'un juge exigeant ou un avocat adverse compétent poserait vraiment — pas des questions faciles. Développe chaque piste de réponse avec un vrai raisonnement, pas juste des mots-clés isolés.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "objections": [
    {
      "origine": "Juge" | "Partie adverse",
      "question": "la question ou objection formulée telle qu'elle serait posée à l'oral",
      "piege": "en une phrase, pourquoi cette question est difficile ou ce qu'elle cherche à démontrer",
      "piste_reponse": "une piste de réponse solide, en mots-clés, jamais un texte entièrement rédigé"
    }
  ],
  "point_le_plus_faible": "le point du dossier le plus vulnérable à l'oral, identifié honnêtement"
}

Règles impératives :
- Les questions doivent être réalistes et exigeantes, pas des questions de complaisance.
- Ne cite jamais une référence juridique qui n'a pas été fournie dans le contexte, sauf en préfixant "À VÉRIFIER : ". Si elle a bien été fournie dans le contexte, cite-la normalement, sans ce préfixe.
- Les pistes de réponse restent des mots-clés et repères, jamais un texte entièrement rédigé.
- Rédige les questions, le piège identifié et le point le plus faible en français soutenu et professionnel.
- Si les informations du dossier sont insuffisantes pour des questions pertinentes, dis-le clairement plutôt que d'inventer des faits."""


def simuler_objections(contexte_dossier: str, contexte_recherche: str | None = None) -> dict:
    """Génère des questions/objections probables pour préparer l'oral."""
    system = SIMULATEUR_SYSTEM_PROMPT
    if contexte_recherche:
        system += contexte_recherche

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=3800,
        system=system,
        messages=[{"role": "user", "content": f"Contexte du dossier :\n{contexte_dossier}"}],
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")

    parsed.setdefault("objections", [])
    return parsed


RESUME_SYSTEM_PROMPT = """Tu es un assistant qui aide un avocat francophone à retrouver rapidement l'essentiel d'un dossier qu'il a accumulé au fil de plusieurs documents importés.

À partir du contenu brut du dossier fourni (qui peut mélanger plusieurs documents importés à des moments différents), produis un résumé complet et exploitable — ne sacrifie pas les détails factuels importants pour la brièveté.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "resume_court": "un résumé de la situation dans son ensemble, aussi développé que nécessaire pour couvrir les éléments importants (plusieurs phrases si le dossier le justifie)",
  "points_cles": ["tous les faits ou éléments importants du dossier, autant que nécessaire — ne te limite pas à un nombre arbitraire"],
  "elements_manquants": ["informations qui semblent manquer pour bien traiter ce dossier, s'il y en a"]
}

Règles impératives :
- Reste strictement factuel : ne déduis rien qui ne soit pas dans le texte fourni.
- Ne cite aucune référence juridique — ce résumé porte sur les faits, pas le droit.
- Rédige en français soutenu et professionnel.
- Si le contenu du dossier est trop pauvre pour un résumé utile, dis-le clairement dans elements_manquants plutôt que d'inventer."""


NOTE_CLIENT_SYSTEM_PROMPT = """Tu rédiges une note explicative destinée directement au client d'un avocat francophone, à partir des éléments de son dossier. Le client n'a aucune formation juridique.

Règles impératives :
- Aucun jargon juridique non expliqué. Si un terme technique est nécessaire, explique-le en quelques mots simples entre parenthèses la première fois qu'il apparaît.
- Registre soutenu et soigné malgré la simplicité — un français correct et professionnel, jamais familier, même en expliquant simplement. Phrases courtes, ton rassurant mais honnête — jamais de fausse promesse sur l'issue de l'affaire.
- Structure la note en 3 parties courtes : "Où en est votre dossier", "Ce que cela signifie concrètement pour vous", "Les prochaines étapes".
- Ne cite aucune référence juridique précise (article de loi, numéro de jurisprudence) — cette note est pour le client, pas pour le dossier judiciaire.
- Reste strictement factuel, basé uniquement sur les informations fournies. N'invente aucun fait ni aucune échéance non mentionnée.
- Respecte la typographie française : guillemets « … », apostrophe typographique ', espace avant ; : ? !."""


CHRONOLOGIE_SYSTEM_PROMPT = """Tu es un assistant qui aide un greffier francophone à structurer la chronologie d'une affaire à partir des documents et faits fournis.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "evenements": [
    {"date": "date de l'événement telle qu'elle apparaît dans le texte, ou 'date non précisée'", "evenement": "description factuelle courte de ce qui s'est passé"}
  ],
  "periode_couverte": "résumé en une phrase de la période couverte par ces événements",
  "elements_manquants": ["dates ou étapes procédurales qui semblent manquantes ou peu claires, s'il y en a"]
}

Règles impératives :
- Trie les événements par ordre chronologique quand les dates le permettent.
- Reste strictement factuel et neutre — ne prends parti pour aucune partie, ton rôle est celui du greffier, pas d'un avocat.
- N'invente aucune date ni aucun événement qui ne figure pas dans le texte fourni.
- Rédige en français soutenu et professionnel.
- Si le texte ne contient aucune date exploitable, dis-le clairement dans elements_manquants plutôt que d'inventer une chronologie."""


def construire_chronologie(contexte_affaire: str) -> dict:
    """Construit une chronologie structurée à partir du contenu d'une affaire."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1800,
        system=CHRONOLOGIE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Contenu de l'affaire :\n{contexte_affaire}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("evenements", [])
    parsed.setdefault("elements_manquants", [])
    return parsed


EXTRACTION_SYSTEM_PROMPT = """Tu es un assistant qui aide un greffier francophone à extraire automatiquement les éléments clés d'un document juridique (dates, noms, références, demandes, décisions).

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "dates": ["liste des dates identifiées dans le document, avec leur contexte bref"],
  "personnes_et_parties": ["noms de personnes physiques ou morales identifiés, avec leur qualité si mentionnée (demandeur, défendeur, témoin...)"],
  "references": ["numéros de dossier, références RG, références de textes de loi ou d'actes cités"],
  "demandes": ["ce qui est demandé au tribunal, s'il y en a"],
  "decisions": ["décisions ou dispositifs mentionnés, s'il y en a"]
}

Règles impératives :
- N'extrais que ce qui est explicitement présent dans le texte — n'invente rien.
- Reste neutre et factuel, sans commentaire ni interprétation.
- Formule chaque élément en français soutenu et professionnel.
- Si une catégorie est vide, retourne une liste vide plutôt que d'inventer un contenu."""


def extraire_elements_cles(texte_document: str) -> dict:
    """Extrait automatiquement dates, noms, références, demandes et
    décisions d'un document juridique."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1500,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Document :\n{texte_document}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    for cle in ("dates", "personnes_et_parties", "references", "demandes", "decisions"):
        parsed.setdefault(cle, [])
    return parsed


CLASSEMENT_SYSTEM_PROMPT = """Tu es un assistant qui aide un greffier francophone à classer un document selon sa nature juridique.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "nature": "un seul mot ou expression courte parmi : assignation, jugement, ordonnance, conclusions, pièce, requête, citation, procès-verbal, autre",
  "justification": "une phrase expliquant pourquoi ce document correspond à cette catégorie",
  "confiance": "Élevée" | "Moyenne" | "Faible"
}

Règles impératives :
- Base-toi uniquement sur des indices explicites du texte (formules types, structure, en-tête).
- Si le document ne correspond clairement à aucune catégorie usuelle, utilise "autre" et explique pourquoi dans la justification.
- Rédige la justification en français soutenu et professionnel.
- N'invente aucun élément qui ne soit pas dans le texte."""


def classifier_document(texte_document: str) -> dict:
    """Classe un document selon sa nature juridique (assignation, jugement,
    ordonnance, conclusions, pièce...)."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=500,
        system=CLASSEMENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Document :\n{texte_document[:4000]}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("nature", "autre")
    parsed.setdefault("justification", "")
    parsed.setdefault("confiance", "Faible")
    return parsed


PV_SYSTEM_PROMPT = """Tu es un assistant qui aide un greffier francophone à rédiger une première version structurée de procès-verbal d'audience, à partir de notes prises pendant l'audience.

Structure ta réponse en texte simple, prêt à relire et compléter, selon ce plan :

PREMIÈRE VERSION — À RELIRE ET COMPLÉTER PAR LE GREFFIER

1. EN-TÊTE
   (juridiction, date, formation — indique [À COMPLÉTER] si l'information ne figure pas dans les notes)

2. PRÉSENCES
   (parties, avocats, témoins mentionnés dans les notes)

3. DÉROULEMENT DES DÉBATS
   (résumé chronologique factuel de ce qui s'est dit et passé)

4. OBSERVATIONS ET PRÉTENTIONS DES PARTIES

5. INCIDENTS
   (s'il y en a — sinon indique "Néant")

6. ISSUE
   (décision, mise en délibéré, renvoi — selon ce qui figure dans les notes)

Règles impératives :
- Reste strictement neutre : ne prends parti pour aucune partie, rapporte les faits tels que notés.
- N'invente RIEN qui ne soit pas dans les notes fournies — utilise "[À COMPLÉTER]" pour tout ce qui manque, plutôt que de deviner.
- Précise en ouverture que ceci est une première version destinée à être relue, complétée et validée par le greffier.
- Rédige dans le registre soutenu et solennel propre aux actes de procédure français.
- N'invente aucune référence de texte de loi ou de procédure.
- Respecte la typographie française : guillemets « … », apostrophe typographique ', espace avant ; : ? !."""


def rediger_pv(notes_audience: str) -> str:
    """Structure des notes d'audience brutes en une première version de
    procès-verbal, à relire et compléter par le greffier."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=2000,
        system=PV_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Notes prises pendant l'audience :\n{notes_audience}"}],
    )
    return response.content[0].text.strip()


REQUISITOIRE_SYSTEM_PROMPT = """Tu es un assistant qui aide un greffier francophone à structurer le contenu d'un réquisitoire du ministère public, à partir de son texte.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "qualification_retenue": "qualification(s) pénale(s) retenue(s) contre le prévenu/accusé, telle(s) qu'elle(s) apparaissent dans le texte",
  "faits_et_elements_invoques": ["faits ou éléments de preuve invoqués à l'appui de l'accusation"],
  "circonstances_aggravantes": ["circonstances aggravantes mentionnées, s'il y en a"],
  "circonstances_attenuantes": ["circonstances atténuantes mentionnées, s'il y en a"],
  "peine_requise": "peine ou mesure demandée par le ministère public, telle qu'elle apparaît dans le texte, ou 'non précisée'",
  "points_attention": ["toute mention procédurale, référence à vérifier ou incohérence à signaler, s'il y en a"]
}

Règles impératives :
- Reste strictement neutre — ne prends parti pour aucune partie, ne commente ni le bien-fondé ni la sévérité du réquisitoire.
- N'extrais que ce qui est explicitement présent dans le texte — n'invente rien.
- Ne cite aucun article de loi précis sans le préfixer de "À VÉRIFIER : ", sauf si tu es très sûr de sa formulation exacte. Ce préfixe doit rester l'exception, pas un réflexe : quand tu es sûr, cite sans lui.
- Rédige chaque élément en français soutenu et professionnel.
- Si une catégorie est vide ou non mentionnée, retourne une liste vide (ou 'non précisée' pour peine_requise) plutôt que d'inventer un contenu."""


def analyser_requisitoire(texte_requisitoire: str) -> dict:
    """Structure le contenu d'un réquisitoire (qualification retenue,
    éléments invoqués, circonstances, peine requise) de façon neutre,
    sans prendre parti — pour le greffier, pas une base de réfutation."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1800,
        system=REQUISITOIRE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Texte du réquisitoire :\n{texte_requisitoire}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("qualification_retenue", "")
    for cle in ("faits_et_elements_invoques", "circonstances_aggravantes", "circonstances_attenuantes", "points_attention"):
        parsed.setdefault(cle, [])
    parsed.setdefault("peine_requise", "non précisée")
    return parsed


RAPPORT_INSTRUCTION_SYSTEM_PROMPT = """Tu es un assistant qui aide un greffier francophone à structurer le contenu d'un rapport d'instruction (ou d'une ordonnance de règlement du juge d'instruction), à partir de son texte.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "actes_instruction": ["actes d'instruction accomplis mentionnés (auditions, expertises, perquisitions, confrontations...), avec leur date si précisée"],
  "elements_a_charge": ["éléments retenus à charge du mis en examen"],
  "elements_a_decharge": ["éléments retenus à décharge, s'il y en a"],
  "mesures_ordonnees": ["mesures ordonnées au cours de l'instruction (contrôle judiciaire, détention provisoire, expertise...)"],
  "sens_propose": "sens de la décision proposée par le rapport (renvoi, non-lieu, requalification...), telle qu'elle apparaît dans le texte, ou 'non précisé'",
  "points_attention": ["toute anomalie, incohérence ou point à vérifier manuellement, s'il y en a"]
}

Règles impératives :
- Reste strictement neutre — ne prends parti pour aucune partie, ne porte aucune appréciation sur le bien-fondé des éléments à charge ou à décharge.
- N'extrais que ce qui est explicitement présent dans le texte — n'invente rien.
- Ne cite aucun article de loi précis sans le préfixer de "À VÉRIFIER : ", sauf si tu es très sûr de sa formulation exacte. Ce préfixe doit rester l'exception, pas un réflexe : quand tu es sûr, cite sans lui.
- Rédige chaque élément en français soutenu et professionnel.
- Si une catégorie est vide ou non mentionnée, retourne une liste vide (ou 'non précisé' pour sens_propose) plutôt que d'inventer un contenu."""


def analyser_rapport_instruction(texte_rapport: str) -> dict:
    """Structure le contenu d'un rapport d'instruction (actes accomplis,
    éléments à charge/à décharge, mesures ordonnées, sens proposé) de
    façon neutre, pour le greffier."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1800,
        system=RAPPORT_INSTRUCTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Texte du rapport d'instruction :\n{texte_rapport}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    for cle in ("actes_instruction", "elements_a_charge", "elements_a_decharge", "mesures_ordonnees", "points_attention"):
        parsed.setdefault(cle, [])
    parsed.setdefault("sens_propose", "non précisé")
    return parsed


def rediger_note_client(contexte_dossier: str) -> str:
    """Rédige une explication en langage simple du dossier, destinée à être
    envoyée directement au client — sans jargon juridique."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1500,
        system=NOTE_CLIENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Éléments du dossier :\n{contexte_dossier}"}],
    )
    return response.content[0].text.strip()


def resumer_dossier(contexte_dossier: str) -> dict:
    """Produit un résumé synthétique d'un dossier, utile après plusieurs
    imports de documents pour retrouver rapidement l'essentiel."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=2200,
        system=RESUME_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Contenu du dossier :\n{contexte_dossier}"}],
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")

    parsed.setdefault("points_cles", [])
    parsed.setdefault("elements_manquants", [])
    return parsed


def generer_plan_plaidoirie(contexte_dossier: str, temps_minutes: int, contexte_recherche: str | None = None) -> dict:
    """Génère un plan de plaidoirie structuré à partir du contexte d'un dossier."""
    system = PLAN_SYSTEM_PROMPT
    if contexte_recherche:
        system += contexte_recherche

    client = _client()
    message = f"Temps de parole imparti : {temps_minutes} minutes.\n\nContexte du dossier :\n{contexte_dossier}"
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=3200,
        system=system,
        messages=[{"role": "user", "content": message}],
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")

    parsed.setdefault("plan", [])
    parsed.setdefault("points_attention", [])
    return parsed


def analyser_conclusions(texte: str, contexte_recherche: str | None = None, jurisprudence_validee: list | None = None) -> dict:
    """
    Envoie le texte des conclusions adverses à Claude et retourne un dict
    {"arguments": [...], "points_attention": [...]}.

    contexte_recherche : bloc de texte optionnel produit par
    recherche_juridique.formater_contexte_pour_prompt() — résultats live
    de Légifrance/Judilibre, injectés en contexte pour orienter l'analyse.

    jurisprudence_validee : liste optionnelle de dicts (reference, resume)
    issus de la base locale, pour des références que vous avez déjà validées
    manuellement (voir db.py) — plus fiable qu'un résultat live non relu.
    """
    system = SYSTEM_PROMPT
    if jurisprudence_validee:
        refs = "\n".join(
            f"- {j['reference']} : {j.get('resume', '')}" for j in jurisprudence_validee
        )
        system += JURISPRUDENCE_CONTEXT_TEMPLATE.format(refs=refs)
    if contexte_recherche:
        system += contexte_recherche

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=3200,
        system=system,
        messages=[{"role": "user", "content": texte}],
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Réponse du modèle non-JSON, impossible à parser : {e}\n\nRéponse brute :\n{raw}"
        )

    parsed.setdefault("arguments", [])
    parsed.setdefault("points_attention", [])
    return parsed


def reviser_texte(texte_original: str, instruction_revision: str) -> str:
    """Révise un texte déjà généré (note client, PV...) selon une
    instruction précise, sans réécrire ce qui n'a pas été demandé de
    changer. Utilisé pour la boucle de révision interactive."""
    system = (
        "Tu révises un document déjà rédigé, selon l'instruction précise donnée par l'utilisateur. "
        "Applique uniquement le changement demandé — ne réécris pas ce qui n'a pas été demandé de "
        "changer, garde le même format et le même ton que le document original. "
        "N'invente aucun fait nouveau qui ne figurait pas déjà dans le document ou l'instruction."
    )
    message = f"Document original :\n{texte_original}\n\nModification demandée :\n{instruction_revision}"

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": message}],
    )
    return response.content[0].text.strip()


TRADUCTION_SYSTEM_PROMPT = """Tu es un traducteur juridique professionnel français ↔ anglais, spécialisé dans les textes de droit et de procédure.

Détecte automatiquement si le texte fourni est en français ou en anglais, puis traduis-le intégralement vers l'AUTRE langue.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "langue_detectee": "fr" | "en",
  "langue_cible": "fr" | "en",
  "texte_traduit": "la traduction intégrale, prête à l'emploi"
}

Règles impératives :
- Traduis le sens, pas mot à mot — un texte juridique traduit doit se lire comme rédigé nativement dans la langue cible, jamais comme une traduction mécanique.
- Préserve le ton, le registre (soutenu et professionnel) et le style du texte original — un texte formel reste formel, un texte simple reste simple.
- Préserve la terminologie juridique précise : utilise l'équivalent reconnu dans la langue cible (ex. "mise en demeure" → "formal notice", "faute grave" → "serious misconduct"), jamais une traduction littérale qui trahirait le sens juridique. Si un terme français n'a pas d'équivalent exact reconnu en anglais (ou inversement), garde le terme original entre parenthèses après sa traduction approximative.
- Conserve la structure du texte (titres, listes, paragraphes, mise en forme **gras**) telle quelle.
- Le marqueur "À VÉRIFIER" lui-même (uniquement ces deux mots) reste identique dans les deux langues, jamais traduit ni supprimé — mais tout le reste de la phrase qui le suit (le contenu signalé comme incertain) DOIT être traduit normalement, comme le reste du texte. N'utilise jamais "À VÉRIFIER" comme prétexte pour laisser une portion du texte non traduite.
- N'ajoute, ne résume et n'omets aucune information — une traduction fidèle, rien de plus.
- Si le texte cible est le français, respecte la typographie française : guillemets « … », apostrophe typographique ', espace avant ; : ? !, tiret d'incise court – (jamais le tiret long —)."""


def traduire_texte(texte: str) -> dict:
    """Détecte automatiquement la langue (français ou anglais) et traduit
    vers l'autre langue, en préservant le ton et la terminologie juridique
    — utilisé pour partager un document généré par Plaid'IA avec une partie
    ou un confrère anglophone, sans passer par un moteur de traduction
    générique moins fiable sur le vocabulaire juridique précis."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=4000,
        system=TRADUCTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Texte à traduire :\n{texte}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("langue_detectee", "")
    parsed.setdefault("langue_cible", "")
    parsed.setdefault("texte_traduit", "")
    return parsed


EDITION_SYSTEM_PROMPT = """Tu es l'assistant d'édition de Plaid'IA. Un professionnel du droit vient d'écrire un message en langage naturel à propos d'un résultat déjà généré par l'outil et actuellement affiché à l'écran (une analyse, un plan de plaidoirie, une note, une chronologie...). Ta tâche : comprendre précisément ce qu'il demande, PAS régénérer tout le résultat par réflexe.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "intent": "modify" | "add" | "delete" | "explain" | "compare" | "clarification",
  "scope": "global" ou le chemin exact d'un champ du résultat actuel -- \"arguments\" (toute la liste), \"arguments[1]\" (un élément de liste), \"accroche\" (un champ scalaire), ou un chemin imbriqué à n'importe quelle profondeur comme \"arguments[0].refutations\" (la liste des réfutations du premier argument) ou \"arguments[0].refutations[1]\" (une réfutation précise) -- privilégie TOUJOURS le chemin le plus profond et le plus étroit possible,
  "operation": "rewrite" | "expand" | "shorten" | "delete" | "add" | "explain" | "compare" | "none",
  "parameters": {"tone": "...", "length": "...", "audience": "...", "autre": "..."},
  "contenu_modifie": la nouvelle valeur du champ ciblé par "scope", dans EXACTEMENT la même forme (mêmes clés) que l'élément original du résultat actuel -- null si intent est "explain", "compare" ou "clarification",
  "reponse_agent": "phrase(s) à afficher dans le fil de discussion -- confirmation courte pour modify/add/delete, explication ou comparaison complète pour explain/compare, question de clarification pour clarification"
}

Règles impératives :
- "cette plaidoirie", "ce résultat", "cet argument", "la conclusion"... sans plus de précision désignent le résultat actuel fourni ci-dessous -- ne redemande jamais ce qui est déjà visible à l'écran.
- Modifie UNIQUEMENT ce qui est demandé. "contenu_modifie" ne doit contenir QUE l'élément ciblé par "scope", jamais le résultat entier, sauf si scope="global" (rare -- seulement pour une demande explicite de tout refaire, ex. "refais tout dans un style plus offensif").
- Distingue une modification locale (un argument, un point du plan, une objection, un événement...) d'une modification globale : privilégie toujours le scope le plus étroit possible qui satisfait la demande.
- Un ajout ("ajoute la jurisprudence pertinente à cet argument", "ajoute cet événement") : scope = le chemin de la liste concernée SANS index final (ex. "arguments[0].refutations" pour ajouter une réfutation au premier argument, ou "arguments" pour ajouter un nouvel argument entier), operation = "add", contenu_modifie = le NOUVEL élément seul, dans la même forme que les éléments existants de cette liste.
- Une suppression ("supprime cette partie", "retire le deuxième point", "retire cette piste de réfutation") : scope = le chemin précis de l'élément visé AVEC son index (ex. "arguments[0].refutations[1]"), operation = "delete", contenu_modifie = null.
- Une demande d'explication ou de justification ("pourquoi cet argument est risqué", "je ne suis pas convaincu") : intent="explain", scope=l'élément concerné, operation="explain", contenu_modifie=null, et développe une vraie réponse argumentée dans "reponse_agent" (identifie la faiblesse, propose éventuellement une alternative) -- ne modifie rien.
- Une comparaison entre plusieurs éléments : intent="compare", scope="global" ou les deux éléments les plus pertinents, contenu_modifie=null, la comparaison elle-même dans "reponse_agent".
- Si la demande est trop ambiguë pour déterminer avec confiance le scope ou l'opération (référence peu claire, plusieurs interprétations aussi plausibles) : intent="clarification", scope="global", operation="none", contenu_modifie=null, et pose UNE question précise dans "reponse_agent" plutôt que de deviner et de risquer de modifier le mauvais élément.
- N'invente jamais un champ ou un index qui n'existe pas dans le résultat actuel fourni.
- Rédige "reponse_agent" en français soutenu et professionnel, jamais familier.
- Si le texte réécrit contient une référence (article, jurisprudence) qui n'est pas dans le résultat original ni dans le contexte du dossier fourni, préfixe-la "À VÉRIFIER : ", exactement comme le reste de l'outil."""


def traiter_message_edition(
    feature: str,
    message: str,
    resultat_actuel: dict,
    contexte_dossier: str = "",
    historique: list[dict] | None = None,
) -> dict:
    """Classifie un message en langage naturel portant sur un résultat déjà
    affiché (feature="conclusions"/"plan"/"simulateur"/"note_client"/...)
    et produit, en un seul appel, l'action structurée correspondante
    ({intent, scope, operation, contenu_modifie, reponse_agent}).

    Ne modifie rien elle-même : c'est app.chat_actions qui valide et
    applique le résultat de cette fonction. Voir
    ARCHITECTURE_CHAT_CONTEXTUEL.md §2.3 pour la distinction
    GLOBAL_UPDATE / LOCAL_UPDATE que ce découpage {scope, operation} permet."""
    contexte = f"Fonctionnalité concernée : {feature}\n\nRésultat actuel affiché à l'écran :\n{json.dumps(resultat_actuel, ensure_ascii=False, indent=2)}"
    if contexte_dossier:
        contexte += f"\n\nContexte du dossier :\n{contexte_dossier}"

    messages = list(historique or [])
    messages.append({"role": "user", "content": f"{contexte}\n\nDemande de l'utilisateur :\n{message}"})

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=3000,
        system=EDITION_SYSTEM_PROMPT,
        messages=messages,
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")

    parsed.setdefault("intent", "clarification")
    parsed.setdefault("scope", "global")
    parsed.setdefault("operation", "none")
    parsed.setdefault("parameters", {})
    parsed.setdefault("contenu_modifie", None)
    parsed.setdefault("reponse_agent", "")
    return parsed


VERIFICATION_PROCEDURALE_SYSTEM_PROMPT = """Tu es un assistant qui aide un professionnel du droit francophone (avocat ou greffier) à vérifier qu'une procédure ne présente pas d'anomalie apparente, à partir du contenu d'une affaire.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "echeances_identifiees": [
    {"echeance": "description de l'échéance ou du délai identifié", "date": "date telle qu'elle apparaît dans le texte, ou 'non précisée'", "statut": "À venir" | "Proche" | "Possiblement dépassée" | "Date incertaine"}
  ],
  "actes_potentiellement_manquants": [
    "étape ou acte de procédure qui semble absent au vu du contexte, avec une brève explication de pourquoi il serait normalement attendu"
  ],
  "points_attention": ["toute anomalie, incohérence ou point à vérifier manuellement, s'il y en a"]
}

Règles impératives :
- Reste strictement neutre — ne prends parti pour aucune partie.
- N'affirme JAMAIS avec certitude qu'un délai est dépassé ou qu'un acte manque : utilise des formulations prudentes ("semble", "pourrait", "à vérifier") car tu ne disposes que d'un extrait du dossier, pas de l'intégralité de la procédure.
- Ne cite aucun article de procédure précis sans le préfixer de "À VÉRIFIER : ", sauf si tu es très sûr de sa formulation exacte. Ce préfixe doit rester l'exception, pas un réflexe : quand tu es sûr, cite sans lui.
- N'invente aucune date ni aucun acte qui ne serait pas déductible du texte fourni.
- Rédige en français soutenu et professionnel.
- Si le contenu de l'affaire est insuffisant pour une vérification utile, dis-le clairement dans points_attention plutôt que d'inventer des anomalies."""


def verifier_procedure(contexte_affaire: str) -> dict:
    """Repère les échéances et actes de procédure potentiellement
    manquants ou à vérifier, à partir du contenu d'une affaire. Reste
    délibérément prudent — signale des pistes à vérifier, jamais des
    certitudes."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1800,
        system=VERIFICATION_PROCEDURALE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Contenu de l'affaire :\n{contexte_affaire}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("echeances_identifiees", [])
    parsed.setdefault("actes_potentiellement_manquants", [])
    parsed.setdefault("points_attention", [])
    return parsed


COHERENCE_SYSTEM_PROMPT = """Tu es un assistant qui aide un greffier francophone à détecter des contradictions factuelles entre plusieurs documents relatifs à une même affaire.

On te fournit les éléments factuels déjà extraits de chaque document (dates, personnes, références, montants, demandes, décisions). Compare-les systématiquement pour repérer les divergences.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "contradictions": [
    {
      "sujet": "ce sur quoi porte la contradiction (ex: montant du loyer, date de l'audience, orthographe d'un nom)",
      "document_1": "ce qui est indiqué dans le premier document concerné",
      "document_2": "ce qui est indiqué dans le second document concerné",
      "gravite": "Élevée" | "Moyenne" | "Faible"
    }
  ],
  "elements_coherents": ["éléments qui apparaissent de façon cohérente dans plusieurs documents, s'il y a lieu de le signaler positivement"],
  "limites_analyse": "précise honnêtement ce que cette comparaison ne permet pas de garantir (ex: ne couvre que les éléments extraits automatiquement, pas l'intégralité du texte)"
}

Règles impératives :
- Ne signale une contradiction QUE si les deux valeurs comparées portent explicitement sur le même sujet/événement/personne — ne compare pas des éléments non comparables.
- La gravité "Élevée" est réservée aux divergences factuelles significatives (montants, dates d'échéance, identité des parties) ; "Faible" pour des différences mineures (formulation, orthographe probablement équivalente).
- Reste strictement neutre, ne prends parti pour aucune partie.
- Rédige en français soutenu et professionnel.
- N'invente aucune contradiction qui ne soit pas clairement déductible des éléments fournis."""


def controler_coherence(elements_par_document: list) -> dict:
    """Compare les éléments factuels extraits de plusieurs documents pour
    détecter des contradictions (dates, montants, noms, références
    divergents pour un même sujet).

    `elements_par_document` est une liste de dicts, chacun avec au moins
    {"nom_document": str, "elements": dict} — le dict "elements" ayant le
    format retourné par extraire_elements_cles()."""
    parties = []
    for doc in elements_par_document:
        parties.append(f"--- {doc['nom_document']} ---")
        for cle, valeurs in doc["elements"].items():
            if valeurs:
                parties.append(f"{cle} : {'; '.join(valeurs)}")
    contenu = "\n".join(parties)

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1800,
        system=COHERENCE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Éléments extraits des documents :\n{contenu}"}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("contradictions", [])
    parsed.setdefault("elements_coherents", [])
    parsed.setdefault("limites_analyse", "")
    return parsed


POSITION_JURISPRUDENCE_SYSTEM_PROMPT = """Tu es un assistant qui aide un avocat francophone à comprendre la position générale de la jurisprudence sur un sujet donné, à partir des décisions trouvées en recherche live.

Réponds en texte structuré, prêt à lire, selon ce plan :

1. POSITION DOMINANTE
   (ce que la jurisprudence retient le plus généralement sur ce sujet, si un courant clair se dégage)

2. NUANCES ET EXCEPTIONS
   (les cas où les tribunaux s'écartent de la position dominante, s'il y en a)

3. ÉVOLUTION RÉCENTE
   (si les décisions trouvées montrent un changement de position dans le temps, signale-le ; sinon indique qu'aucune évolution notable n'apparaît dans les éléments disponibles)

4. DÉCISIONS DE RÉFÉRENCE
   (liste les références les plus pertinentes trouvées, avec leur apport respectif)

Règles impératives :
- Base-toi UNIQUEMENT sur les décisions et textes fournis dans le contexte de recherche — ne cite jamais une jurisprudence non présente dans ce contexte, sauf en préfixant "À VÉRIFIER : ". Si elle est bien présente dans ce contexte, cite-la normalement, sans ce préfixe.
- Si les résultats de recherche sont insuffisants ou contradictoires pour dégager une position claire, dis-le explicitement plutôt que d'inventer une tendance.
- Reste factuel et neutre — décris ce que dit la jurisprudence, ne donne pas de conseil stratégique de défense (ce n'est pas le rôle de cette fonction).
- Structure chaque section en listes à puces plutôt qu'en blocs denses dès que le contenu s'y prête, et mets en gras les éléments clés (référence de décision, principe dégagé).
- La longueur de chaque section doit s'adapter à ce que les résultats de recherche permettent réellement de dire — bref si peu d'éléments, plus développé si le contexte le justifie.
- Rédige en français soutenu et professionnel.

Qualité rédactionnelle :
- Varie la longueur des phrases — évite les suites de phrases très courtes ou, à l'inverse, des phrases surchargées de propositions.
- Emploie un vocabulaire précis mais jamais artificiellement sophistiqué.
- Évite de répéter le même mot ou la même tournure d'une phrase à l'autre.
- Utilise des connecteurs logiques (cependant, ainsi, en revanche, de plus, néanmoins...) avec modération.

Typographie française :
- Une espace avant ; : ? ! — jamais avant , ni . .
- Guillemets français « … » pour toute citation, jamais de guillemets droits "...".
- Apostrophe typographique ' (jamais l'apostrophe droite ').
- Tiret d'incise court – pour une incise dans une phrase, jamais le tiret long —."""


def consulter_position_jurisprudence(sujet: str, contexte_recherche: str) -> str:
    """Synthétise la position générale de la jurisprudence sur un sujet,
    à partir du contexte de recherche live (Légifrance/Judilibre) déjà
    récupéré. Contrairement à repondre_question, reste volontairement
    neutre et informatif plutôt que stratégique."""
    system = POSITION_JURISPRUDENCE_SYSTEM_PROMPT
    if contexte_recherche:
        system += contexte_recherche
    else:
        system += "\n\nAucun résultat de recherche live disponible — indique-le clairement et n'invente aucune décision."

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1800,
        system=system,
        messages=[{"role": "user", "content": f"Sujet à traiter :\n{sujet}"}],
    )
    return response.content[0].text.strip()


NOTIONS_JURIDIQUES_SYSTEM_PROMPT = """Tu es un assistant qui prépare une recherche de jurisprudence à partir de faits décrits par un avocat francophone. Tu ne réponds pas à la question juridique toi-même — tu prépares seulement la recherche qui va suivre.

Réponds UNIQUEMENT en JSON valide, sans texte avant ni après, sans balises markdown, avec exactement ces clés :
{
  "domaine": "domaine juridique concerné, ex. Droit des contrats",
  "qualification_juridique": "qualification juridique précise en une courte phrase, ex. Inexécution contractuelle",
  "mots_cles_recherche": ["3 à 6 mots-clés ou expressions courtes", "en français juridique précis", "à utiliser tels quels dans un moteur de recherche de jurisprudence"],
  "but": "reprend exactement la valeur du paramètre but fournie, ou 'neutre' si aucune n'a été précisée"
}

Règles :
- Les mots-clés doivent être de VRAIS termes juridiques de recherche (ex. "inexécution contractuelle", "mise en demeure", "clause résolutoire") — jamais une phrase complète ni la reformulation mot à mot des faits.
- Si les faits ne permettent pas d'identifier clairement un domaine, indique ta meilleure estimation et reste prudent dans la qualification plutôt que d'inventer une certitude."""


def identifier_notions_juridiques(faits: str, but: str = "") -> dict:
    """Étape préparatoire avant la recherche de jurisprudence : à partir des
    faits décrits en langage libre, identifie le domaine juridique, la
    qualification, et surtout de VRAIS mots-clés de recherche — plutôt que
    d'envoyer la phrase brute de l'avocat telle quelle à Judilibre/Légifrance,
    ce qui donnait des résultats moins pertinents."""
    client = _client()
    contenu = f"Faits : {faits}"
    if but:
        contenu += f"\n\nBut de la recherche précisé par l'avocat : {but}"
    else:
        contenu += "\n\nAucun but n'a été précisé par l'avocat."

    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=400,
        system=NOTIONS_JURIDIQUES_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": contenu}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("domaine", "")
    parsed.setdefault("qualification_juridique", "")
    parsed.setdefault("mots_cles_recherche", [])
    parsed.setdefault("but", but or "neutre")
    return parsed


JURISPRUDENCE_CONSULT_SYSTEM_PROMPT = """Tu es un assistant qui aide un avocat à comprendre ce que disent les sources juridiques sur une situation donnée — celles-ci peuvent couvrir plusieurs juridictions (France, OHADA, Union européenne...).

À partir de la question ou situation décrite, et du contexte fourni (organisé par source, avec un en-tête "--- Source : X ---" pour chacune), synthétise ce que ces sources disent — pas ton opinion personnelle, seulement ce qu'elles rapportent.

Structure impérativement ta réponse ainsi :

Question juridique : <la qualification juridique fournie>
Objectif retenu : <le but fourni, ou "neutre — aucun objectif précisé" si absent>

Puis, pour CHAQUE décision de jurisprudence présente dans le contexte fourni (jamais une décision qui n'y figure pas), une fiche ainsi structurée, dans l'ordre du plus utile au moins utile compte tenu de l'objectif retenu :

– <référence complète : juridiction, date, n° d'arrêt> –
Faits : <résumé bref des faits de cette décision>
Solution : <ce que la juridiction a effectivement décidé>
Principe dégagé : <le principe juridique qu'on peut en tirer>
Pertinence par rapport aux faits de l'avocat : forte / moyenne / faible
Favorable / Défavorable / Neutre : <seulement si un objectif autre que "neutre" a été précisé — sinon écris "Neutre (aucun objectif précisé)". Cette étiquette doit être honnête : une décision qui va contre la position visée doit être marquée "Défavorable", jamais habillée en "Neutre" pour ménager l'avocat — connaître les décisions défavorables est essentiel à sa préparation.>
Source : <l'URL vérifiable fournie dans le contexte>

Règles impératives :
- Base-toi UNIQUEMENT sur les éléments fournis dans le contexte — ne cite jamais une décision, une référence, une date ou un numéro d'arrêt qui n'y figure pas explicitement, sous aucun prétexte. Si tu ne peux pas remplir un champ avec une information du contexte, écris "À VÉRIFIER : information non trouvée dans les sources" plutôt que de l'inventer. À l'inverse, dès que l'information figure clairement dans le contexte, indique-la normalement, sans "À VÉRIFIER".
- Si plusieurs sources/juridictions sont présentes dans le contexte, regroupe les fiches par source ("Côté droit français :", "Côté OHADA :"...) — ne mélange jamais deux systèmes juridiques différents dans une même fiche.
- Si le contexte ne contient AUCUNE décision pertinente pour la question posée, dis-le clairement et explicitement plutôt que d'inventer une décision ou une tendance.
- Distingue une position bien établie (plusieurs décisions convergentes) d'une position isolée — sois honnête sur ce niveau de certitude.
- Reste factuel sur ce que chaque décision dit ; l'étiquette Favorable/Défavorable/Neutre est une aide à la lecture, pas un jugement de valeur sur la décision elle-même.
- Rédige l'intégralité de la réponse — y compris les titres de section eux-mêmes ("Question juridique", "Objectif retenu", "Faits", "Solution", "Principe dégagé", etc.) — en français soutenu et professionnel, le registre attendu d'un écrit entre confrères.
- Mets en gras (avec des doubles astérisques, ex. **ainsi**) les éléments qui méritent d'être repérés en un coup d'œil dans chaque fiche — la référence de la décision, le principe dégagé, l'étiquette de pertinence.
- La longueur de chaque fiche doit s'adapter à ce que le contexte permet réellement de dire : reste bref si peu d'éléments sont disponibles, développe davantage si le contexte fourni le justifie — sans jamais combler par de l'invention.

Qualité rédactionnelle :
- Varie la longueur des phrases dans les champs "Faits" et "Solution" — évite les suites de phrases très courtes.
- Emploie un vocabulaire précis mais jamais artificiellement sophistiqué ; évite de répéter le même mot d'une fiche à l'autre.

Typographie française :
- Une espace avant ; : ? ! — jamais avant , ni . .
- Guillemets français « … » pour toute citation, jamais de guillemets droits "...".
- Apostrophe typographique ' (jamais l'apostrophe droite ').
- Tiret d'incise court – pour une incise dans une phrase, jamais le tiret long —."""


def consulter_jurisprudence(question: str, contexte_recherche: str, qualification: str = "", but: str = "") -> str:
    """Répond à une question en se basant spécifiquement sur la
    jurisprudence trouvée en direct — pas sur les connaissances générales
    du modèle. Produit une fiche structurée par décision (référence, faits,
    solution, principe, pertinence, étiquette favorable/défavorable/neutre
    selon l'objectif de recherche, source vérifiable) plutôt qu'une simple
    synthèse en prose."""
    system = JURISPRUDENCE_CONSULT_SYSTEM_PROMPT
    if contexte_recherche:
        system += "\n\n" + contexte_recherche
    else:
        system += "\n\nAucune jurisprudence n'a été trouvée en direct pour cette question."

    consigne = f"Faits/question : {question}"
    if qualification:
        consigne += f"\n\nQualification juridique identifiée : {qualification}"
    consigne += f"\n\nObjectif retenu pour cette recherche : {but or 'neutre — aucun objectif précisé'}"

    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=2200,
        system=system,
        messages=[{"role": "user", "content": consigne}],
    )
    return response.content[0].text.strip()


NOTES_INTELLIGENTES_SYSTEM_PROMPT = """Tu aides un professionnel du droit à organiser des notes de travail rapides et informelles liées à un dossier.

À partir du texte brut fourni (notes prises en vrac, parfois désordonnées), produis :
1. Une version structurée et claire de ces notes.
2. La liste des actions à faire identifiées dans le texte.
3. Les autres points importants à retenir qui ne sont pas des actions.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "note_structuree": "version reformulée et organisée des notes, en conservant tout le contenu factuel",
  "actions_a_faire": ["action identifiée 1", "action identifiée 2"],
  "points_a_retenir": ["point important non actionnable, s'il y en a"]
}

Règles impératives :
- Ne supprime AUCUNE information du texte original — reformule, n'oublie rien de substantiel.
- N'invente aucune action ni aucun fait qui ne soit pas dans le texte fourni.
- Reformule "note_structuree" en français soutenu et professionnel, même si les notes d'origine sont informelles.
- Si aucune action claire n'est identifiable, retourne une liste vide plutôt que d'en inventer."""


def traiter_notes(notes_brutes: str) -> dict:
    """Structure des notes de travail brutes et en extrait les actions à
    faire — sans rien inventer ni omettre du contenu original."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=1500,
        system=NOTES_INTELLIGENTES_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": notes_brutes}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    parsed.setdefault("note_structuree", notes_brutes)
    parsed.setdefault("actions_a_faire", [])
    parsed.setdefault("points_a_retenir", [])
    return parsed


INTENTION_SYSTEM_PROMPT = """Tu es un routeur d'intention pour un outil d'aide juridique. Un avocat vient de taper une demande en langage naturel pendant qu'il travaille sur un dossier déjà ouvert. Détermine quelle action il veut effectuer.

Actions disponibles (utilise EXACTEMENT ce code) :
- "importer" : importer/ajouter des documents au dossier
- "analyser" : analyser des conclusions adverses
- "resumer" : résumer le dossier
- "plan" : générer un plan de plaidoirie (peut préciser une durée en minutes)
- "simulateur" : simuler des questions/objections probables
- "rapport" : générer le rapport complet
- "note" : prendre une note de travail
- "notes_consulter" : consulter les notes déjà prises
- "note_client" : rédiger une note pour le client en langage simple
- "export" : exporter les faits bruts du dossier
- "domaine" : modifier le domaine du dossier
- "menu" : afficher le menu numéroté (si la demande est ambiguë, vide, ou hors sujet)
- "quitter" : changer de dossier ou revenir à l'accueil

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "action": "un des codes ci-dessus",
  "duree_minutes": nombre ou null,
  "confiance": "haute" | "basse",
  "reformulation": "courte phrase confirmant ce que tu as compris, à afficher à l'utilisateur"
}

Règles impératives :
- "confiance": "basse" si la demande est ambiguë, très courte, ou pourrait correspondre à plusieurs actions.
- Si tu ne comprends vraiment pas, utilise action="menu" avec confiance="basse"."""


def interpreter_intention(texte: str) -> dict:
    """Interprète une demande en langage naturel et détermine quelle
    action du menu dossier elle correspond, avec un niveau de confiance."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=300,
        system=INTENTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": texte}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"action": "menu", "duree_minutes": None, "confiance": "basse", "reformulation": ""}
    parsed.setdefault("action", "menu")
    parsed.setdefault("duree_minutes", None)
    parsed.setdefault("confiance", "basse")
    parsed.setdefault("reformulation", "")
    return parsed


STYLE_ADVERSE_SYSTEM_PROMPT = """Tu es un assistant qui aide un avocat francophone à analyser la manière dont sont rédigées des conclusions adverses — pas leur contenu juridique, mais leur style et leur rhétorique. Cette analyse linguistique complète l'analyse juridique classique : elle révèle des points de faiblesse dans la manière dont l'argumentation est formulée, qui peuvent se traduire en angles d'attaque à l'audience.

Analyse le texte fourni selon ces axes :

1. Langage de couverture (hedging) : expressions qui atténuent l'engagement de l'auteur ("il semblerait que", "dans une certaine mesure", "en principe") — souvent un signe que l'auteur n'est pas pleinement sûr de son argument, même si le ton paraît assuré.
2. Affirmations absolues : emplois de termes catégoriques ("jamais", "toujours", "en toute hypothèse", "sans aucun doute") — souvent risqués juridiquement, car une seule exception suffit à les invalider.
3. Voix passive ou formulations impersonnelles : quand elles semblent utilisées pour éviter de nommer clairement qui a fait quoi ("il a été convenu que...", "il apparaît que...") — peut indiquer une volonté de diluer une responsabilité.
4. Ruptures de registre ou d'argumentation : changements de ton, répétitions inhabituelles, ou passages qui semblent moins maîtrisés que le reste du texte — peuvent signaler un point sur lequel l'auteur est en difficulté.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown, selon ce schéma exact :

{
  "langage_de_couverture": [{"citation": "extrait exact du texte", "commentaire": "ce que cela révèle"}],
  "affirmations_absolues": [{"citation": "extrait exact du texte", "commentaire": "pourquoi c'est risqué et attaquable"}],
  "voix_passive_suspecte": [{"citation": "extrait exact du texte", "commentaire": "ce qui est potentiellement dissimulé"}],
  "ruptures_registre": [{"citation": "extrait exact ou description du passage", "commentaire": "ce que cela peut signaler"}],
  "synthese_strategique": "2-3 phrases de synthèse : qu'est-ce que cette analyse stylistique révèle globalement sur les points faibles ou les incertitudes de la partie adverse, et comment un avocat pourrait s'en servir concrètement à l'audience"
}

Règles impératives :
- Cite des extraits RÉELS et EXACTS du texte fourni — jamais une citation inventée ou approximative.
- Reste factuel sur l'analyse linguistique : décris ce que le texte fait, sans prêter d'intentions psychologiques certaines à son auteur (utilise "peut suggérer", "semble indiquer", jamais des affirmations catégoriques sur les intentions de l'auteur).
- Rédige tes commentaires et la synthèse en français soutenu et professionnel.
- Si un axe d'analyse ne révèle rien de notable dans ce texte précis, retourne une liste vide pour cet axe plutôt que d'inventer un exemple.
- Cette analyse est un outil d'aide à la réflexion stratégique, pas une preuve juridique — elle ne doit jamais être présentée comme telle."""


def analyser_style_adverse(texte: str) -> dict:
    """Analyse linguistique et rhétorique de conclusions adverses —
    langage de couverture, affirmations absolues, voix passive suspecte,
    ruptures de registre. Complète l'analyse juridique classique par un
    angle stylistique, exploitant l'expertise en analyse du discours."""
    client = _client()
    response = client.messages.create(
        model=MODEL_ACTIF,
        max_tokens=2500,
        system=STYLE_ADVERSE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": texte}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse du modèle non-JSON : {e}\n\nRéponse brute :\n{raw}")
    for cle in ("langage_de_couverture", "affirmations_absolues", "voix_passive_suspecte", "ruptures_registre"):
        parsed.setdefault(cle, [])
    parsed.setdefault("synthese_strategique", "")
    return parsed
