"""
deps.py — Petits utilitaires partagés entre routers : récupération d'un
dossier (404 si absent), construction du "contexte dossier" textuel envoyé
aux fonctions d'analyse — reproduit fidèlement `_contexte_dossier()` de
gui.py — et extraction générique d'un fichier uploadé (voir
AUDIT_IMPORT_EXPORT.md §10 : un seul endroit pour valider/extraire un
upload, réutilisé par tous les routers qui acceptent un document, plutôt
qu'une copie par fonctionnalité).
"""

import os
import tempfile
from pathlib import Path

from app.bootstrap import ROOT_DIR  # noqa: F401

import analyse as legacy_analyse
import db
import extract as legacy_extract
from fastapi import HTTPException, UploadFile

# --- Libellés bilingues des sections déterministes (diagnostic/stratégie) ---
# Ce texte est construit ici en Python, PAS par un appel à Claude -- la
# directive de langue d'analyse._directive_langue() ne s'y applique donc
# pas, il faut le traduire explicitement. Les données du dossier lui-même
# (faits saisis, domaine, partie représentée...) restent affichées telles
# quelles : ce sont des données du dossier, pas des libellés d'interface.
_LIBELLES = {
    "faits": {"fr": "Faits", "en": "Facts"},
    "parties": {"fr": "Parties", "en": "Parties"},
    "partie_representee": {"fr": "Partie représentée", "en": "Party represented"},
    "stade_procedure": {"fr": "Stade de la procédure", "en": "Procedural stage"},
    "objectif_client": {"fr": "Objectif du client", "en": "Client's objective"},
    "arguments_adverses_deja_analyses": {"fr": "Arguments adverses déjà analysés :", "en": "Adverse arguments already analysed:"},
    "dossier_domaine": {"fr": "Dossier « {nom} », domaine : {domaine}.", "en": "Case “{nom}”, area of law: {domaine}."},
    "diagnostic_titre": {"fr": "Diagnostic\nFaits et éléments disponibles :", "en": "Diagnosis\nFacts and information available:"},
    "diagnostic_forces": {
        "fr": "Forces, faiblesses et risques : les arguments et leurs niveaux de risque sont listés ci-dessus.",
        "en": "Strengths, weaknesses and risks: the arguments and their risk levels are listed above.",
    },
    "diagnostic_objections": {
        "fr": "Objections identifiées : chaque objection et sa piste de réponse doivent être examinées contradictoirement.",
        "en": "Objections identified: each objection and its suggested response should be examined adversarially.",
    },
    "diagnostic_reponse": {
        "fr": "Réponse juridique produite : elle doit être confrontée aux sources et aux faits du dossier.",
        "en": "Legal response produced: it must be checked against the sources and the facts of the case.",
    },
    "strategie_combative_titre": {
        "fr": "Stratégie combative pour {posture}\nBalayage systématique des moyens disponibles, sans en écarter aucun a priori.{objectif_texte}",
        "en": "Combative strategy for {posture}\nSystematic review of every available line of argument, none discarded a priori.{objectif_texte}",
    },
    "objectif_declare": {"fr": " Objectif déclaré : {objectif}.", "en": " Stated objective: {objectif}."},
    "aucun_moyen_axe": {
        "fr": "Aucun moyen exploitable identifié sur cet axe pour ce dossier.",
        "en": "No usable argument identified on this front for this case.",
    },
    "moyens_improbables_titre": {
        "fr": "Moyens improbables (non écartés -- à l'avocat seul de décider de les soulever)",
        "en": "Long-shot arguments (not discarded -- it is for the lawyer alone to decide whether to raise them)",
    },
    "reponses_arguments_adverses_titre": {"fr": "Réponses aux arguments adverses", "en": "Responses to the adverse arguments"},
    "probabilite_succes": {"fr": "probabilité de succès", "en": "likelihood of success"},
    "cout_risque": {"fr": "coût/risque", "en": "cost/risk"},
    "strategie_generique_titre": {
        "fr": "Stratégie pour {posture}\nMoyens à soulever en priorité, pièces à produire, objections à anticiper et arguments adverses à neutraliser.{objectif_texte}",
        "en": "Strategy for {posture}\nArguments to raise as a priority, evidence to produce, objections to anticipate, and adverse arguments to neutralise.{objectif_texte}",
    },
    "strategie_aucune_partie": {
        "fr": "Stratégie\nAucune partie n'est renseignée : la stratégie n'est pas orientée et le résultat reste présenté de manière générale.",
        "en": "Strategy\nNo party has been specified: the strategy is not oriented and the result stays presented in general terms.",
    },
    "axe_procedure": {"fr": "Procédure", "en": "Procedure"},
    "axe_preuve": {"fr": "Preuve", "en": "Evidence"},
    "axe_fond": {"fr": "Fond", "en": "Merits"},
    "axe_quantum": {"fr": "Quantum", "en": "Quantum"},
    "prob_forte": {"fr": "Forte", "en": "High"},
    "prob_moyenne": {"fr": "Moyenne", "en": "Medium"},
    "prob_faible": {"fr": "Faible", "en": "Low"},
    "prob_improbable": {"fr": "Improbable", "en": "Long shot"},
}

_AXE_VERS_CLE = {"Procédure": "axe_procedure", "Preuve": "axe_preuve", "Fond": "axe_fond", "Quantum": "axe_quantum"}
_PROBABILITE_VERS_CLE = {"Forte": "prob_forte", "Moyenne": "prob_moyenne", "Faible": "prob_faible", "Improbable": "prob_improbable"}


def _l(cle: str) -> str:
    """Libellé bilingue -- la langue vient du même ContextVar que
    analyse._directive_langue() (posé par le middleware X-Langue, voir
    backend/app/main.py), retombe sur le français si la clé ou la langue
    n'est pas reconnue."""
    entree = _LIBELLES.get(cle, {})
    return entree.get(legacy_analyse.langue_requete(), entree.get("fr", cle))


def _traduire_valeur(valeur: str, correspondance: dict[str, str]) -> str:
    """Traduit une valeur d'énumération produite par le LLM (axe, probabilité
    de succès) pour l'affichage -- la valeur elle-même reste en français dans
    les données (le schéma des prompts la fixe ainsi, voir
    STRATEGIE_COMBATIVE_SYSTEM_PROMPT), seul son libellé affiché change."""
    cle = correspondance.get(valeur)
    return _l(cle) if cle else valeur

# Formats acceptés par l'extraction de texte générique (voir
# extract.py::extract_text) -- PDF, Word, Excel, texte, images. Même liste
# que frontend/src/lib/fichiers.ts::EXTENSIONS_DOCUMENT, à garder synchronisées.
EXTENSIONS_DOCUMENT_AUTORISEES = {".pdf", ".docx", ".xlsx", ".xls", ".txt", ".png", ".jpg", ".jpeg", ".webp"}

# §13 (ARCHITECTURE_CHAT_CONTEXTUEL.md) : limite de taille explicite --
# UploadFile n'en impose aucune par défaut, un fichier sans limite lu
# entièrement en mémoire via .read() est une vraie surface d'abus.
MAX_TAILLE_FICHIER_UPLOAD = 20 * 1024 * 1024  # 20 Mo


async def extraire_texte_upload(fichier: UploadFile) -> str:
    """Validation du format et de la taille, écriture dans un fichier
    temporaire, extraction, nettoyage -- puis traduction des erreurs
    d'extraction (fichier vide, corrompu) en réponses HTTP propres plutôt
    que la 500 générique que renverrait sinon le handler de secours de
    main.py. DocumentNumeriseError n'est PAS interceptée ici : elle doit
    remonter telle quelle jusqu'au handler dédié de main.py.

    Point d'entrée UNIQUE pour tout endpoint qui accepte un upload de
    document dans l'application (dossiers, corpus juridique...) -- ne pas
    dupliquer cette logique ailleurs."""
    suffix = Path(fichier.filename or "").suffix.lower()
    if suffix not in EXTENSIONS_DOCUMENT_AUTORISEES:
        raise HTTPException(
            status_code=415,
            detail=f"Format non supporté : {suffix or '(aucun)'}. Formats acceptés : {legacy_extract.FORMATS_SUPPORTES}",
        )

    contenu = await fichier.read(MAX_TAILLE_FICHIER_UPLOAD + 1)
    if len(contenu) > MAX_TAILLE_FICHIER_UPLOAD:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (limite : {MAX_TAILLE_FICHIER_UPLOAD // (1024 * 1024)} Mo).",
        )
    if not contenu:
        raise HTTPException(status_code=422, detail="Le fichier est vide.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contenu)
            tmp_path = tmp.name

        try:
            return legacy_extract.extract_text(tmp_path)
        except legacy_extract.DocumentNumeriseError:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Impossible de lire ce fichier : il semble corrompu ou dans un format inattendu ({e}).",
            )
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def get_dossier_or_404(dossier_id: int) -> dict:
    """Récupère un dossier en base ou lève une 404 JSON exploitable côté front."""
    row = db.get_dossier(dossier_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Dossier {dossier_id} introuvable.")
    return dict(row)


def construire_contexte_dossier(dossier: dict) -> str:
    """Reproduit PlaidIAApp._contexte_dossier() (gui.py) : agrège faits,
    parties et la dernière analyse enregistrée en un texte que les fonctions
    d'analyse.py utilisent comme `contexte_dossier` / `contexte_affaire`."""
    parts = []
    if dossier.get("faits"):
        parts.append(f"{_l('faits')} : {dossier['faits']}")
    if dossier.get("parties"):
        parts.append(f"{_l('parties')} : {dossier['parties']}")
    if dossier.get("partie_representee"):
        parts.append(f"{_l('partie_representee')} : {dossier['partie_representee']}")
    if dossier.get("stade_procedure"):
        parts.append(f"{_l('stade_procedure')} : {dossier['stade_procedure']}")
    if dossier.get("objectif"):
        parts.append(f"{_l('objectif_client')} : {dossier['objectif']}")

    analyses = db.get_analyses_for_dossier(dossier["id"])
    if analyses:
        derniere = analyses[0]
        parts.append(_l("arguments_adverses_deja_analyses"))
        for arg in derniere["arguments"]:
            parts.append(f"- [{arg.get('risque', '?')}] {arg.get('resume', '')}")

    return "\n".join(parts) if parts else _l("dossier_domaine").format(nom=dossier["nom"], domaine=dossier.get("domaine", ""))


_AXES_STRATEGIQUES = ["Procédure", "Preuve", "Fond", "Quantum"]


def _formater_moyen(moyen: dict, *, avec_axe: bool = False) -> str:
    prefixe = f"{_traduire_valeur(moyen.get('axe', '?'), _AXE_VERS_CLE)} — " if avec_axe else ""
    probabilite = _traduire_valeur(moyen.get("probabilite_succes", "?"), _PROBABILITE_VERS_CLE)
    entete = f"- {prefixe}{moyen.get('moyen', '')} ({_l('probabilite_succes')} : {probabilite} — {_l('cout_risque')} : {moyen.get('cout_risque', '?')})"
    developpement = (moyen.get("developpement") or "").strip()
    return f"{entete}\n  {developpement}" if developpement else entete


def _formater_strategie_combative(strategie_combative: dict, posture: str, objectif_texte: str) -> str:
    """Construit le texte combatif et exhaustif de la stratégie -- voir le
    complément posture/stratégie : balayage systématique des quatre axes
    (procédure, preuve, fond, quantum), moyens jamais supprimés (les
    improbables sont listés à part), et une réponse proposée pour chaque
    argument adverse identifié."""
    moyens = strategie_combative.get("moyens") or []
    reponses = strategie_combative.get("reponses_arguments_adverses") or []

    parties = [_l("strategie_combative_titre").format(posture=posture, objectif_texte=objectif_texte)]

    for axe in _AXES_STRATEGIQUES:
        moyens_axe = [m for m in moyens if m.get("axe") == axe and m.get("probabilite_succes") != "Improbable"]
        libelle_axe = _l(_AXE_VERS_CLE[axe])
        if moyens_axe:
            bloc = "\n".join(_formater_moyen(m) for m in moyens_axe)
            parties.append(f"{libelle_axe}\n{bloc}")
        else:
            parties.append(f"{libelle_axe}\n{_l('aucun_moyen_axe')}")

    moyens_improbables = [m for m in moyens if m.get("probabilite_succes") == "Improbable"]
    if moyens_improbables:
        bloc = "\n".join(_formater_moyen(m, avec_axe=True) for m in moyens_improbables)
        parties.append(f"{_l('moyens_improbables_titre')}\n{bloc}")

    if reponses:
        bloc = "\n".join(
            f"- {r.get('argument_adverse', '')} → {r.get('reponse', '')}" for r in reponses
        )
        parties.append(f"{_l('reponses_arguments_adverses_titre')}\n{bloc}")

    return "\n\n".join(parties)


def structurer_sortie_strategique(
    resultat: dict, dossier: dict, feature: str, strategie_combative: dict | None = None
) -> dict:
    """Ajoute deux sections stables sans orienter le diagnostic par défaut.

    `strategie_combative` : résultat optionnel de
    analyse.generer_strategie_combative() (voir les routers de
    /api/analyse) -- balayage combatif et exhaustif procédure/preuve/fond/
    quantum pour la partie représentée. Absent en mode démo et quand aucune
    partie n'est renseignée : la stratégie retombe alors sur un texte
    générique, jamais sur un appel réseau depuis cette fonction pure."""
    diagnostic_parts = [_l("diagnostic_titre"), construire_contexte_dossier(dossier)]
    if resultat.get("arguments"):
        diagnostic_parts.append(_l("diagnostic_forces"))
    if resultat.get("objections"):
        diagnostic_parts.append(_l("diagnostic_objections"))
    if resultat.get("reponse"):
        diagnostic_parts.append(_l("diagnostic_reponse"))

    posture = (dossier.get("partie_representee") or "").strip()
    if posture:
        objectif = (dossier.get("objectif") or "").strip()
        objectif_texte = _l("objectif_declare").format(objectif=objectif) if objectif else ""
        if strategie_combative and (strategie_combative.get("moyens") or strategie_combative.get("reponses_arguments_adverses")):
            strategie = _formater_strategie_combative(strategie_combative, posture, objectif_texte)
        else:
            strategie = _l("strategie_generique_titre").format(posture=posture, objectif_texte=objectif_texte)
    else:
        strategie = _l("strategie_aucune_partie")
    return {**resultat, "diagnostic": "\n\n".join(diagnostic_parts), "strategie": strategie}
