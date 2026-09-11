"""
recherche_lexicometrique.py — Recherche jurisprudentielle par similarité
lexicométrique déterministe (fréquence de termes + cosinus), sur demande
explicite de l'utilisateur (consigne fournie verbatim) : jamais un taux
"estimé" par un modèle de langage, toujours un calcul réel sur le texte des
décisions de la base -- exactement ce que la consigne exige ("zéro
invention... chaque chiffre doit provenir d'un calcul réel, jamais d'une
estimation").

Complémentaire de recherche_juridique.py (recherche live Légifrance/
Judilibre, aucun score de similarité) -- ici, on compare un texte de départ
(argument ou paragraphe) aux décisions déjà validées manuellement en base
(db.get_jurisprudence_validee, voir db.py) et on calcule un vrai taux.
Portée volontairement limitée à cette source à ce stade (la plus fiable,
déjà relue par l'avocat) -- le corpus multi-source et Judilibre en direct
pourront s'ajouter plus tard comme sources de candidats supplémentaires,
sans changer le calcul lui-même.
"""

import math
import re
from collections import Counter

import db

SEUIL_PERTINENCE = 0.5  # 50 % -- en dessous, la décision est écartée sans être mentionnée (règle 3 de la consigne).

# Mots vides français -- volontairement une liste courte et généraliste
# (articles, pronoms, prépositions les plus fréquents), pas un lexique
# linguistique complet : l'objectif est d'écarter le bruit grammatical pour
# que la similarité porte sur le vocabulaire juridique réellement
# discriminant (termes de qualification, articles cités...), pas de faire
# de l'analyse linguistique fine.
MOTS_VIDES = frozenset({
    "le", "la", "les", "l", "un", "une", "des", "de", "du", "d", "au", "aux", "à",
    "et", "ou", "mais", "donc", "or", "ni", "car",
    "ce", "cet", "cette", "ces", "cela", "ça", "ceci",
    "il", "elle", "ils", "elles", "on", "nous", "vous", "je", "tu",
    "se", "sa", "son", "ses", "leur", "leurs", "lui", "y", "en",
    "que", "qui", "quoi", "dont", "où", "comme", "si",
    "dans", "sur", "sous", "par", "pour", "avec", "sans", "entre", "vers", "chez", "depuis", "pendant", "selon",
    "est", "sont", "être", "avoir", "a", "ont", "été", "étant",
    "ne", "pas", "plus", "très", "tout", "toute", "tous", "toutes",
    "qu", "s", "n", "c", "j", "m", "t",
})

# Mots accentués français inclus -- les termes juridiques ("préjudice",
# "réquisitoire", "responsabilité"...) en dépendent. Mots composés à trait
# d'union préservés comme un seul token (ex. "mise-en-demeure"), pas coupés
# en deux mots séparés qui perdraient le sens du terme.
_RE_TOKEN = re.compile(
    r"[a-zàâäéèêëïîôöùûüÿçœæ]+(?:-[a-zàâäéèêëïîôöùûüÿçœæ]+)*", re.IGNORECASE
)


def _tokeniser(texte: str) -> list[str]:
    """Découpe `texte` en tokens comparables : minuscules, mots vides
    retirés, tokens d'une seule lettre écartés (bruit, jamais un terme
    juridique discriminant)."""
    tokens = [t.lower() for t in _RE_TOKEN.findall(texte or "")]
    return [t for t in tokens if t not in MOTS_VIDES and len(t) > 1]


def _similarite_cosinus(vecteur_a: Counter, vecteur_b: Counter) -> float:
    """Cosinus entre deux vecteurs de fréquence de termes -- capture le
    vocabulaire partagé ET son poids relatif (un terme répété compte plus
    qu'un terme cité une fois), pas seulement une intersection binaire.
    Retourne 0.0 si l'un des textes ne produit aucun token (rien à comparer)."""
    termes_communs = set(vecteur_a) & set(vecteur_b)
    if not termes_communs:
        return 0.0
    produit_scalaire = sum(vecteur_a[t] * vecteur_b[t] for t in termes_communs)
    norme_a = math.sqrt(sum(v * v for v in vecteur_a.values()))
    norme_b = math.sqrt(sum(v * v for v in vecteur_b.values()))
    if norme_a == 0 or norme_b == 0:
        return 0.0
    return produit_scalaire / (norme_a * norme_b)


def _termes_partages(vecteur_a: Counter, vecteur_b: Counter, max_termes: int = 6) -> list[str]:
    """Termes présents dans les deux textes, triés par fréquence combinée
    décroissante -- ce sont les "termes clés partagés" exigés par le format
    de sortie (règle 4 de la consigne) pour justifier le taux calculé."""
    termes_communs = set(vecteur_a) & set(vecteur_b)
    tries = sorted(termes_communs, key=lambda t: vecteur_a[t] + vecteur_b[t], reverse=True)
    return tries[:max_termes]


def comparer_a_la_jurisprudence_validee(texte_depart: str, domaine: str | None = None) -> list[dict]:
    """
    Compare `texte_depart` (un argument ou un paragraphe de conclusions) à
    chaque décision de db.get_jurisprudence_validee(domaine), par similarité
    lexicométrique (fréquence de termes + cosinus -- voir le commentaire
    d'en-tête du module, jamais une estimation du modèle).

    Ne retourne QUE les décisions dont le taux dépasse SEUIL_PERTINENCE
    (50 %, règle 3 de la consigne) -- une décision en dessous est écartée
    sans apparaître dans le résultat. Trié du plus pertinent au moins
    pertinent (règle 4), avec le rang assigné après ce filtrage/tri.

    Retourne une liste de dicts :
    {"rang": int, "reference": str, "taux_similarite": float (0-100, un
    chiffre après la virgule), "termes_cles_partages": [str, ...]}

    Liste vide si aucune décision ne dépasse le seuil, ou si la base est
    vide -- à traiter comme "aucune correspondance", jamais comme une
    erreur (règle 5 de la consigne : le signaler, ne jamais forcer un
    résultat faible).
    """
    vecteur_depart = Counter(_tokeniser(texte_depart))
    decisions = db.get_jurisprudence_validee(domaine)

    resultats = []
    for decision in decisions:
        vecteur_decision = Counter(_tokeniser(decision.get("resume") or ""))
        taux = _similarite_cosinus(vecteur_depart, vecteur_decision)
        if taux < SEUIL_PERTINENCE:
            continue
        resultats.append({
            "reference": decision["reference"],
            "taux_similarite": round(taux * 100, 1),
            "termes_cles_partages": _termes_partages(vecteur_depart, vecteur_decision),
        })

    resultats.sort(key=lambda r: r["taux_similarite"], reverse=True)
    for rang, resultat in enumerate(resultats, start=1):
        resultat["rang"] = rang
    return resultats


def formater_resultats(resultats: list[dict]) -> str:
    """
    Formate le résultat de comparer_a_la_jurisprudence_validee() selon le
    format de sortie exact demandé :
    [RANG] - [RÉFÉRENCE DÉCISION] - [TAUX DE SIMILARITÉ %] - [TERMES CLÉS PARTAGÉS]

    Message explicite si `resultats` est vide (règle 5) -- jamais une
    chaîne vide silencieuse qui laisserait croire à un oubli plutôt qu'à
    une absence réelle de correspondance.
    """
    if not resultats:
        return "Aucune décision de la base ne dépasse le seuil de pertinence de 50 % -- aucune correspondance retenue."

    return "\n".join(
        f"[{r['rang']}] - [{r['reference']}] - [{r['taux_similarite']}%] - "
        f"[{', '.join(r['termes_cles_partages'])}]"
        for r in resultats
    )
