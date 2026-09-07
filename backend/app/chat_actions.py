"""
chat_actions.py — Couche de validation entre le LLM et l'état applicatif,
pour le chat contextuel (voir ARCHITECTURE_CHAT_CONTEXTUEL.md §2.4).

Le modèle ne modifie jamais un résultat directement : il propose
{scope, operation, contenu_modifie}, et ce module vérifie que la portée
demandée existe réellement dans le résultat actuel AVANT d'appliquer quoi
que ce soit. Volontairement générique (pas de schéma codé en dur par
fonctionnalité) : la validation lit la forme réelle de `resultat_actuel`
au moment de l'appel, donc elle reste valable pour n'importe quel nouveau
schéma de sortie ajouté plus tard sans modifier ce fichier.

Convention de "scope" (chemin à la Python, sans les guillemets) :
- "global"                          -> tout le résultat.
- "<champ>"                          -> un champ scalaire de premier niveau (ex. "accroche").
- "<champ>[<index>]"                 -> un élément d'une liste de premier niveau (ex. "arguments[1]").
- "<champ>[<index>].<souschamp>"     -> un champ imbriqué dans un élément de liste
                                         (ex. "arguments[0].refutations" pour la liste
                                         des réfutations du premier argument).
- et ainsi de suite, à n'importe quelle profondeur (ex.
  "arguments[0].refutations[1]", "arguments[0].raisonnement.regle_applicable").
Testé en conditions réelles : un modèle interrogé sur "ajoute une piste de
réfutation à cet argument" choisit naturellement ce niveau de précision
(scope="arguments[0].refutations", operation="add") plutôt que de
réécrire l'argument entier — exactement le comportement "LOCAL_UPDATE"
recherché, d'où le support de la profondeur arbitraire plutôt qu'un seul
niveau.
"""

import copy
import re

OPERATIONS_AUTORISEES = {"rewrite", "expand", "shorten", "delete", "add", "explain", "compare", "none"}

_RE_SEGMENT = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)(\[(\d+)\])?$")


class ActionInvalide(ValueError):
    """Le scope ou l'opération proposés par le modèle ne correspondent pas
    au résultat actuel — l'action n'est jamais appliquée dans ce cas."""


def _analyser_chemin(scope: str) -> list[tuple[str, int | None]]:
    """Découpe "arguments[0].refutations[1]" en [("arguments", 0), ("refutations", 1)]."""
    segments = []
    for partie in scope.split("."):
        m = _RE_SEGMENT.match(partie)
        if not m:
            raise ActionInvalide(f"Scope mal formé : {scope!r} (segment {partie!r} invalide).")
        nom, _, idx = m.groups()
        segments.append((nom, int(idx) if idx is not None else None))
    return segments


def _naviguer(resultat_actuel: dict, segments: list[tuple[str, int | None]], feature: str):
    """Parcourt `resultat_actuel` selon `segments`, en vérifiant à chaque
    étape que le champ/l'index existe réellement. Retourne (conteneur_parent,
    nom_du_dernier_champ, index_final_ou_None) — le triplet dont
    valider_action/appliquer_patch ont besoin pour lire ou écrire la cible
    exacte, sans jamais toucher au reste de la structure."""
    courant = resultat_actuel
    chemin_lisible = []
    for i, (nom, idx) in enumerate(segments):
        if not isinstance(courant, dict) or nom not in courant:
            chemin_lisible.append(nom)
            raise ActionInvalide(f"Le champ {'.'.join(chemin_lisible)!r} n'existe pas dans le résultat actuel de {feature!r}.")
        valeur = courant[nom]
        dernier = i == len(segments) - 1

        if idx is None:
            chemin_lisible.append(nom)
            if dernier:
                return courant, nom, None
            courant = valeur
            continue

        chemin_lisible.append(f"{nom}[{idx}]")
        if not isinstance(valeur, list):
            raise ActionInvalide(f"Le champ {'.'.join(chemin_lisible[:-1] + [nom])!r} n'est pas une liste — un index ne s'applique pas ici.")
        if not (0 <= idx < len(valeur)):
            raise ActionInvalide(f"Index hors limites pour {nom!r} : {idx} (liste de {len(valeur)} élément(s)).")
        if dernier:
            return valeur, idx, "index"  # conteneur = la liste elle-même, clé = l'index
        courant = valeur[idx]

    raise ActionInvalide("Scope vide.")


def valider_action(feature: str, scope: str, operation: str, resultat_actuel: dict) -> None:
    """Lève ActionInvalide si l'action proposée ne peut pas être appliquée
    en l'état. N'applique rien — seulement une vérification préalable."""
    if operation not in OPERATIONS_AUTORISEES:
        raise ActionInvalide(f"Opération non reconnue : {operation!r}.")

    if scope == "global":
        return

    segments = _analyser_chemin(scope)
    conteneur, cle, mode_index = _naviguer(resultat_actuel, segments, feature)

    if mode_index == "index":
        # `conteneur` est la liste, `cle` est l'index déjà validé par _naviguer.
        return

    # `cle` est un nom de champ scalaire ou de liste, `conteneur[cle]` sa valeur.
    valeur = conteneur[cle]
    if operation == "add":
        if not isinstance(valeur, list):
            raise ActionInvalide(f"Le champ {cle!r} n'est pas une liste — « add » ne s'y applique pas.")
        return
    if isinstance(valeur, list):
        raise ActionInvalide(f"Le champ {cle!r} est une liste — précisez un index (ex. « {cle}[0] »).")
    if not isinstance(valeur, (str, int, float, type(None))):
        raise ActionInvalide(f"Le champ {cle!r} a une structure trop complexe pour une modification ciblée — utilisez scope=\"global\".")


def appliquer_patch(resultat_actuel: dict, scope: str, operation: str, contenu_modifie) -> dict:
    """Applique une action déjà validée par valider_action() et retourne un
    NOUVEAU dict (le résultat actuel n'est jamais modifié en place, pour
    qu'un appel qui échoue à mi-chemin ne laisse jamais un état partiel)."""
    if scope == "global":
        if not isinstance(contenu_modifie, dict):
            raise ActionInvalide("Une mise à jour globale doit fournir un objet complet en contenu_modifie.")
        return contenu_modifie

    resultat = copy.deepcopy(resultat_actuel)
    segments = _analyser_chemin(scope)
    conteneur, cle, mode_index = _naviguer(resultat, segments, "?")

    if mode_index == "index":
        liste = conteneur  # la liste elle-même
        if operation == "delete":
            liste.pop(cle)
        else:
            liste[cle] = contenu_modifie
        return resultat

    if operation == "add":
        conteneur[cle] = conteneur[cle] + [contenu_modifie]
    else:
        conteneur[cle] = contenu_modifie
    return resultat
