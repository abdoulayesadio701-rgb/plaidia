"""
anonymisation.py — Pseudonymisation des noms de personnes AVANT l'envoi d'un
texte à un modèle externe (Claude, ou tout autre fournisseur), pour les
utilisateurs qui activent cette option sur une analyse.

Objectif et limites, à lire avant tout usage réel (voir aussi la page
Confidentialité du front, `frontend/src/pages/ConfidentialitePage.tsx`) :

- **Détection 100 % locale**, aucun appel réseau : ni Claude ni aucun autre
  service n'est utilisé pour repérer les noms -- sans quoi les vrais noms
  partiraient quand même vers un tiers pour cette seule étape, ce qui
  viderait la fonctionnalité de son sens.
- **Heuristique, pas un vrai NER** : détection par civilité (M., Mme,
  Maître...) et par motif « Prénom NOM » (prénom reconnu dans un
  répertoire, nom en majuscules ou capitalisé) -- convention très
  répandue dans les actes et conclusions français. Ce n'est PAS exhaustif :
  un nom isolé sans civilité ni majuscule caractéristique peut échapper à
  la détection, et un nom propre qui n'est pas une personne (lieu,
  société) peut être détecté à tort. À utiliser comme réduction du risque,
  jamais comme garantie d'anonymat total.
- **Réversible par construction** : chaque occurrence détectée est
  remplacée par un pseudonyme stable ("Personne A", "Personne B"...),
  cohérent sur tout le texte, et la correspondance permet de reconstituer
  le texte original -- c'est le résultat FINAL (avec les vrais noms) qui
  est affiché à l'utilisateur et, le cas échéant, enregistré dans son
  dossier. Seul ce qui part vers le modèle reste pseudonymisé.
- **Portée** : noms de personnes physiques uniquement. Ne traite pas les
  adresses, numéros de téléphone, dates de naissance ni autres données
  personnelles -- voir la page Confidentialité pour le périmètre exact.
"""

import re

# Répertoire volontairement large (France, espace OHADA/Afrique
# francophone, cohérent avec le périmètre de Plaid'IA) mais non exhaustif --
# un prénom absent de cette liste n'est détecté que via le motif civilité
# (ex. "M. Traoré") ou le motif NOM en majuscules (ex. "Amina KEITA").
PRENOMS = frozenset(
    p.lower()
    for p in (
        "Jean", "Pierre", "Michel", "Alain", "Philippe", "Bernard", "André", "Louis", "Marc", "Nicolas",
        "François", "Laurent", "Christophe", "Julien", "Thomas", "Daniel", "Patrick", "Olivier", "Stéphane",
        "Vincent", "Antoine", "Guillaume", "Frédéric", "Sébastien", "David", "Maxime", "Paul", "Hugo",
        "Lucas", "Arthur", "Gabriel", "Raphaël", "Léo", "Nathan", "Théo", "Enzo", "Mathis", "Baptiste",
        "Marie", "Isabelle", "Sylvie", "Catherine", "Nathalie", "Françoise", "Monique", "Christine",
        "Nicole", "Martine", "Anne", "Brigitte", "Sophie", "Valérie", "Sandrine", "Céline", "Julie",
        "Camille", "Émilie", "Aurélie", "Charlotte", "Léa", "Chloé", "Manon", "Inès", "Sarah", "Clara",
        "Amadou", "Ibrahima", "Mamadou", "Moussa", "Ousmane", "Cheikh", "Alassane", "Abdoulaye", "Seydou",
        "Souleymane", "Boubacar", "Modibo", "Yacouba", "Issa", "Lamine", "Aliou", "Thierno", "Oumar",
        "Fatou", "Aminata", "Aïcha", "Mariam", "Awa", "Bineta", "Khadija", "Coumba", "Ndeye", "Rokhaya",
        "Kadidiatou", "Salimata", "Adama", "Kwame", "Kofi", "Yaw", "Emmanuel", "Emmanuella", "Chidi",
        "Chinwe", "Ngozi", "Ifeoma", "Fatoumata",
    )
)

CIVILITES = ("Madame", "Monsieur", "Mesdames", "Messieurs", "Mme", "M", "Mlle", "Me", "Maître", "Dr")

_MOT_CAPITALISE = r"[A-ZÀ-Ý][\wà-ÿ'\-]*"
_MOT_MAJUSCULES = r"[A-ZÀ-Ý][A-ZÀ-Ý'\-]+"

# 1. Civilité + 1 ou 2 mots capitalisés : "M. Diallo", "Maître Jean Dupont".
# Le 2e mot ne doit pas être lui-même une civilité (sinon "M. Nom Mme Nom2"
# collée sans ponctuation ferait avaler "Mme" par le nom de la première
# personne, empêchant la seconde d'être détectée).
_RE_CIVILITE = r"(?:" + "|".join(re.escape(c) for c in CIVILITES) + r")"
_RE_CIVILITE_NOM = re.compile(
    r"\b" + _RE_CIVILITE + r"\.?\s+(" + _MOT_CAPITALISE + r"(?:\s+(?!" + _RE_CIVILITE + r"\.?\s)" + _MOT_CAPITALISE + r")?)\b"
)
# 2. "Prénom NOM" -- nom en majuscules, convention des actes juridiques français.
_RE_PRENOM_NOM_MAJ = re.compile(r"\b(" + _MOT_CAPITALISE + r")\s+(" + _MOT_MAJUSCULES + r")\b")
# 3. "Prénom Nom" -- uniquement si le premier mot est un prénom du répertoire,
# pour limiter les faux positifs (deux mots capitalisés qui se suivent sont
# très fréquents pour autre chose qu'un nom de personne : "Cour Cassation"...).
_RE_PRENOM_NOM_GAZETTEER = re.compile(r"\b(" + _MOT_CAPITALISE + r")\s+(" + _MOT_CAPITALISE + r")\b")


def _lettres(mot: str) -> int:
    return sum(1 for c in mot if c.isalpha())


def _detecter_candidats(texte: str) -> list[tuple[int, int, str]]:
    """Renvoie une liste de (debut, fin, nom_detecte) -- les segments qui
    ressemblent à un nom de personne, sans chevauchement (le premier motif
    qui matche à une position donnée l'emporte)."""
    occupe = [False] * len(texte)
    candidats: list[tuple[int, int, str]] = []

    def _marquer(debut: int, fin: int, nom: str) -> None:
        if any(occupe[debut:fin]):
            return
        for i in range(debut, fin):
            occupe[i] = True
        candidats.append((debut, fin, nom))

    for m in _RE_CIVILITE_NOM.finditer(texte):
        _marquer(m.start(1), m.end(1), m.group(1))
    for m in _RE_PRENOM_NOM_MAJ.finditer(texte):
        if _lettres(m.group(2)) >= 2:
            _marquer(m.start(), m.end(), f"{m.group(1)} {m.group(2)}")
    for m in _RE_PRENOM_NOM_GAZETTEER.finditer(texte):
        if m.group(1).lower() in PRENOMS and _lettres(m.group(2)) >= 2:
            _marquer(m.start(), m.end(), f"{m.group(1)} {m.group(2)}")

    return sorted(candidats)


def _cle_regroupement(nom: str) -> str:
    """Deux mentions partagent le même pseudonyme si l'une contient l'autre
    (ex. 'Diallo' et 'M. Amadou Diallo') -- clé = dernier mot, en minuscules,
    sous l'hypothèse que le nom de famille est répété plus souvent que le
    prénom dans un même document."""
    return nom.split()[-1].lower()


def anonymiser_texte(texte: str) -> tuple[str, dict[str, str]]:
    """Remplace chaque nom de personne détecté par un pseudonyme stable
    ("Personne A", "Personne B"...). Renvoie (texte_anonymise, mapping) où
    `mapping` associe chaque pseudonyme à la forme la plus complète
    rencontrée pour cette personne (utilisée par `deanonymiser`)."""
    if not texte:
        return texte, {}

    candidats = _detecter_candidats(texte)
    if not candidats:
        return texte, {}

    forme_complete_par_cle: dict[str, str] = {}
    ordre: list[str] = []
    vues: set[str] = set()

    for _debut, _fin, nom in candidats:
        cle = _cle_regroupement(nom)
        if cle not in vues:
            vues.add(cle)
            ordre.append(cle)
        # La forme la plus longue rencontrée sert de "vrai nom" restitué --
        # généralement la plus complète et la plus lisible pour l'utilisateur.
        if len(nom) > len(forme_complete_par_cle.get(cle, "")):
            forme_complete_par_cle[cle] = nom

    pseudonyme_par_cle = {cle: _pseudonyme(i) for i, cle in enumerate(ordre)}

    morceaux = []
    curseur = 0
    for debut, fin, nom in candidats:
        morceaux.append(texte[curseur:debut])
        morceaux.append(pseudonyme_par_cle[_cle_regroupement(nom)])
        curseur = fin
    morceaux.append(texte[curseur:])

    mapping = {pseudonyme_par_cle[cle]: forme_complete_par_cle[cle] for cle in ordre}
    return "".join(morceaux), mapping


def _pseudonyme(indice: int) -> str:
    """0 -> 'Personne A', 25 -> 'Personne Z', 26 -> 'Personne AA'..."""
    lettres = []
    n = indice
    while True:
        n, r = divmod(n, 26)
        lettres.append(chr(ord("A") + r))
        if n == 0:
            break
        n -= 1
    return "Personne " + "".join(reversed(lettres))


def deanonymiser(valeur, mapping: dict[str, str]):
    """Reconstitue les vrais noms dans `valeur` -- une chaîne, ou une
    structure JSON (dict/list) parcourue récursivement, comme le renvoient
    les fonctions d'analyse (arguments, points_attention, vérification...).
    Sans effet si `mapping` est vide (rien n'a été anonymisé)."""
    if not mapping:
        return valeur
    if isinstance(valeur, str):
        for pseudonyme, vrai_nom in mapping.items():
            valeur = valeur.replace(pseudonyme, vrai_nom)
        return valeur
    if isinstance(valeur, dict):
        return {k: deanonymiser(v, mapping) for k, v in valeur.items()}
    if isinstance(valeur, list):
        return [deanonymiser(v, mapping) for v in valeur]
    return valeur
