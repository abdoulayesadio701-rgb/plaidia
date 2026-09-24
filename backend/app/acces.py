"""
acces.py : mot de passe d'accès optionnel à l'API.

Si la variable d'environnement ACCESS_PASSWORD est définie, toute requête
vers /api/* doit porter l'en-tête X-Acces-Mot-De-Passe avec cette valeur,
sinon elle reçoit une 401. Sans cette variable (cas par défaut, dont les
tests et le développement local), rien ne change.

Pourquoi : un déploiement public qui n'est pas en mode démo utiliserait la
clé Anthropic du serveur pour n'importe quel visiteur. Ce mot de passe
limite l'accès à ceux qui le connaissent. C'est une barrière simple, pas un
système de comptes : tout le monde partage le même mot de passe et voit les
mêmes dossiers.

Exemptions : /api/health (sonde de disponibilité de l'hébergeur) et
/api/config (le front doit savoir si un mot de passe est demandé, avant d'en
afficher le formulaire). Les requêtes OPTIONS (préflight CORS) passent aussi.
"""

import hmac
import os

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

EN_TETE_ACCES = "x-acces-mot-de-passe"
CHEMINS_LIBRES = {"/api/health", "/api/config"}


def mot_de_passe_requis() -> str | None:
    """Lu à chaque appel (pas à l'import) pour rester testable."""
    valeur = os.environ.get("ACCESS_PASSWORD", "").strip()
    return valeur or None


def acces_autorise(en_tete: str | None) -> bool:
    attendu = mot_de_passe_requis()
    if attendu is None:
        return True
    if not en_tete:
        return False
    # Comparaison à temps constant, pour ne rien laisser deviner par la durée.
    return hmac.compare_digest(en_tete.strip().encode("utf-8"), attendu.encode("utf-8"))


class AccesMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        chemin = request.url.path
        if (
            chemin.startswith("/api/")
            and chemin not in CHEMINS_LIBRES
            and request.method != "OPTIONS"
            and not acces_autorise(request.headers.get(EN_TETE_ACCES))
        ):
            # Import tardif : deps.py importe une grande partie du projet.
            from app.deps import libelle

            return JSONResponse(status_code=401, content={"detail": libelle("acces_refuse")})
        return await call_next(request)
