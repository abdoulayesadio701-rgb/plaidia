"""
legifrance.py — Consultation en direct des textes de loi français via l'API
Légifrance, hébergée sur le portail PISTE (DILA).

Prérequis :
  1. Créer un compte sur https://piste.gouv.fr
  2. Créer une application, activer l'API "Légifrance" dessus
  3. Récupérer client_id et client_secret
  4. export LEGIFRANCE_CLIENT_ID="..."
     export LEGIFRANCE_CLIENT_SECRET="..."

Documentation officielle :
  https://piste.gouv.fr/api-dila-legifrance/
"""

import os
import time
import requests
from pathlib import Path
import paths

SANDBOX_OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
PRODUCTION_OAUTH_URL = "https://oauth.piste.gouv.fr/api/oauth/token"

SANDBOX_API_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
PRODUCTION_API_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"

CREDS_FILE = paths.base_dir() / "legifrance_creds.txt"

_token_cache = {"access_token": None, "expires_at": 0}


def _env():
    return os.environ.get("LEGIFRANCE_ENV", "sandbox").lower()


def _oauth_url():
    return PRODUCTION_OAUTH_URL if _env() == "production" else SANDBOX_OAUTH_URL


def _api_url():
    return PRODUCTION_API_URL if _env() == "production" else SANDBOX_API_URL


def _get_credentials():
    """Lit client_id/client_secret depuis l'environnement, sinon depuis
    legifrance_creds.txt (2 lignes : client_id puis client_secret)."""
    client_id = os.environ.get("LEGIFRANCE_CLIENT_ID")
    client_secret = os.environ.get("LEGIFRANCE_CLIENT_SECRET")
    if (not client_id or not client_secret) and CREDS_FILE.exists():
        lines = CREDS_FILE.read_text(encoding="utf-8").strip().splitlines()
        if len(lines) >= 2:
            client_id = client_id or lines[0].strip()
            client_secret = client_secret or lines[1].strip()
    return client_id, client_secret


def _get_token() -> str:
    """Récupère un jeton OAuth2 (client_credentials), avec mise en cache simple."""
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 30:
        return _token_cache["access_token"]

    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        raise EnvironmentError(
            "Identifiants Légifrance introuvables. Soit définissez LEGIFRANCE_CLIENT_ID "
            "et LEGIFRANCE_CLIENT_SECRET, soit créez un fichier legifrance_creds.txt "
            "dans ce dossier avec le client_id sur la première ligne et le client_secret sur la seconde."
        )

    resp = requests.post(
        _oauth_url(),
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)
    return _token_cache["access_token"]


def _headers():
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def search_texte(query: str, page_size: int = 10) -> dict:
    """Recherche plein-texte dans les codes et textes consolidés (fonds CODE)."""
    payload = {
        "recherche": {
            "champs": [{
                "typeChamp": "ALL",
                "criteres": [{"typeRecherche": "UN_DES_MOTS", "valeur": query, "operateur": "ET"}],
                "operateur": "ET",
            }],
            "pageNumber": 1,
            "pageSize": page_size,
            "sort": "PERTINENCE",
            "typePagination": "DEFAUT",
        },
        "fond": "CODE_DATE",
    }
    resp = requests.post(f"{_api_url()}/search", headers=_headers(), json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_article(article_id: str) -> dict:
    """Récupère le contenu intégral d'un article par son identifiant LEGIARTI..."""
    resp = requests.post(
        f"{_api_url()}/consult/getArticle",
        headers=_headers(),
        json={"id": article_id},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def rechercher_articles(query: str, max_results: int = 5) -> list[dict]:
    """
    Recherche des articles de loi pertinents pour `query`.
    Retourne une liste de dicts {reference, texte, source} — jamais stockée,
    utilisée uniquement en contexte immédiat d'une analyse.
    """
    results = search_texte(query, page_size=max_results)
    hits = results.get("results", [])

    articles = []
    for hit in hits:
        code_title = None
        titles = hit.get("titles", [])
        if titles:
            code_title = titles[0].get("title")

        for section in hit.get("sections", []):
            for extract in section.get("extracts", []):
                if len(articles) >= max_results:
                    return articles
                article_id = extract.get("id")
                num = extract.get("num", "")
                values = extract.get("values", [])
                texte = " ".join(values).replace("[...]", "…") if values else ""
                texte = " ".join(texte.split())[:500]
                if not texte:
                    continue
                reference = f"{code_title} - Article {num}" if code_title else f"Article {num}"
                articles.append({
                    "reference": reference,
                    "texte": texte,
                    "source": f"https://www.legifrance.gouv.fr/codes/article_lc/{article_id}" if article_id else "",
                })
    return articles
