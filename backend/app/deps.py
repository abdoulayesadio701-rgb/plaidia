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

import db
import extract as legacy_extract
from fastapi import HTTPException, UploadFile

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
        parts.append(f"Faits : {dossier['faits']}")
    if dossier.get("parties"):
        parts.append(f"Parties : {dossier['parties']}")

    analyses = db.get_analyses_for_dossier(dossier["id"])
    if analyses:
        derniere = analyses[0]
        parts.append("Arguments adverses déjà analysés :")
        for arg in derniere["arguments"]:
            parts.append(f"- [{arg.get('risque', '?')}] {arg.get('resume', '')}")

    return "\n".join(parts) if parts else f"Dossier « {dossier['nom']} », domaine : {dossier.get('domaine', '')}."
