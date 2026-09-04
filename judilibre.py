"""
judilibre.py — Collecte de jurisprudence depuis l'API publique Judilibre
(Cour de cassation), hébergée sur le portail PISTE.

Prérequis :
  1. Créer un compte sur https://piste.gouv.fr
  2. Activer l'API "Judilibre" pour votre application Sandbox (ou Production)
  3. Récupérer votre KeyId depuis le portail PISTE
  4. export JUDILIBRE_KEY_ID="votre-key-id"

Documentation officielle :
  https://github.com/Cour-de-cassation/judilibre-search
"""

import os
import requests

SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"
PRODUCTION_URL = "https://api.piste.gouv.fr/cassation/judilibre/v1.0"

from pathlib import Path
import paths
KEY_FILE = paths.base_dir() / "judilibre_key.txt"


def _env():
    return os.environ.get("JUDILIBRE_ENV", "sandbox").lower()


def _base_url():
    return PRODUCTION_URL if _env() == "production" else SANDBOX_URL


def _headers():
    key_id = os.environ.get("JUDILIBRE_KEY_ID")
    if not key_id and KEY_FILE.exists():
        key_id = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key_id:
        raise EnvironmentError(
            "Clé Judilibre introuvable. Soit définissez JUDILIBRE_KEY_ID, "
            "soit créez un fichier judilibre_key.txt dans ce dossier contenant uniquement votre KeyId."
        )
    return {"accept": "application/json", "KeyId": key_id}


def search_decisions(query: str, page_size: int = 10, page: int = 0) -> dict:
    """Recherche de décisions par mots-clés. Retourne la réponse JSON brute."""
    resp = requests.get(
        f"{_base_url()}/search",
        headers=_headers(),
        params={"query": query, "page_size": page_size, "page": page},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def get_decision(decision_id: str) -> dict:
    """Récupère le détail complet d'une décision (texte, zones, métadonnées)."""
    resp = requests.get(
        f"{_base_url()}/decision",
        headers=_headers(),
        params={"id": decision_id},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def _extract_summary(decision: dict, max_chars: int = 400) -> str:
    """Extrait un résumé court à partir de la zone 'motivations' si disponible,
    sinon des premiers caractères du texte intégral."""
    text = decision.get("text", "")
    zones = decision.get("zones") or {}
    motivations = zones.get("motivations")
    if motivations:
        frag = motivations[0]
        snippet = text[frag["start"]:frag["end"]]
    else:
        snippet = text
    snippet = " ".join(snippet.split())
    return snippet[:max_chars] + ("…" if len(snippet) > max_chars else "")


def _format_reference(decision: dict) -> str:
    """Construit une référence lisible, ex: 'Cass. soc., 12 mars 2020, n° 18-19.827'."""
    jurisdiction = decision.get("jurisdiction", "")
    chamber = decision.get("chamber", "")
    date = decision.get("decision_date", "")
    number = decision.get("number", "") or decision.get("numbers", [""])[0]
    parts = [p for p in [jurisdiction, chamber] if p]
    ref = " ".join(parts)
    if date:
        ref += f", {date}"
    if number:
        ref += f", n° {number}"
    return ref.strip(", ").strip()


def collecter_jurisprudence(query: str, domaine: str = "", max_results: int = 10) -> list[dict]:
    """
    Recherche puis récupère le détail des décisions correspondant à `query`,
    et retourne une liste de dicts prêts à insérer en base :
    {reference, resume, domaine, source}

    Ne valide RIEN automatiquement — à vous de relire et valider chaque entrée
    avant que l'agent puisse s'en servir en contexte de citation.
    """
    results = search_decisions(query, page_size=max_results)
    decisions = results.get("results", [])

    collected = []
    for item in decisions:
        decision_id = item.get("id")
        if not decision_id:
            continue
        try:
            full = get_decision(decision_id)
        except requests.HTTPError:
            continue
        reference = _format_reference(full)
        resume = _extract_summary(full)
        source = f"https://www.courdecassation.fr/decision/{decision_id}"
        collected.append({
            "reference": reference or f"Décision {decision_id}",
            "resume": resume,
            "domaine": domaine,
            "source": source,
        })
    return collected
