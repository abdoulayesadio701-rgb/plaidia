"""
main.py — Point d'entrée de l'API FastAPI de Plaid'IA.

Réutilise tels quels analyse.py, db.py, recherche_juridique.py, judilibre.py,
extract.py et export.py (racine du projet) via app.bootstrap — aucun de ces
fichiers n'est réécrit ni copié.

Lancement : voir backend/README.md (uvicorn app.main:app --reload).
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Charge backend/.env AVANT tout import des modules métier, pour que
# ANTHROPIC_API_KEY / JUDILIBRE_KEY_ID / LEGIFRANCE_CLIENT_ID / ... soient
# déjà dans os.environ quand analyse.py / judilibre.py / legifrance.py les
# lisent (ils lisent os.environ.get(...) à chaque appel, donc l'ordre exact
# importe peu, mais charger tôt évite toute surprise).
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

from app.bootstrap import ROOT_DIR  # noqa: E402  (après load_dotenv, avant les imports racine)

import analyse as legacy_analyse  # noqa: E402
import db  # noqa: E402
import extract as legacy_extract  # noqa: E402
from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from slowapi import Limiter  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402
from slowapi.middleware import SlowAPIMiddleware  # noqa: E402
from slowapi.util import get_remote_address  # noqa: E402

from app import demo, demo_data  # noqa: E402
from app.routers import analyse, chat, documents, dossiers, epingles, greffier, intention, jurisprudence, notes, versions  # noqa: E402
from app.security_guard import DemandeRefusee  # noqa: E402


def _ensemencer_dossier_demo():
    """Ajoute le dossier fictif de démonstration s'il n'existe pas déjà --
    idempotent et jamais destructeur, contrairement à
    db.reinitialiser_donnees_demo() (voir demo.DEMO_RESET_DB)."""
    deja_present = any(d["nom"] == demo_data.NOM_DOSSIER_DEMO for d in db.list_dossiers())
    if not deja_present:
        db.create_dossier(
            nom=demo_data.DOSSIER_DEMO["nom"],
            domaine=demo_data.DOSSIER_DEMO["domaine"],
            parties=demo_data.DOSSIER_DEMO["parties"],
            faits=demo_data.DOSSIER_DEMO["faits"],
            numero_dossier=demo_data.DOSSIER_DEMO["numero_dossier"],
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if demo.mode_demo_serveur() and demo.DEMO_RESET_DB:
        # Mode démo avec réinitialisation explicitement confirmée (valeur
        # par défaut dès que DEMO_MODE=true, sauf DEMO_RESET_DB=false) :
        # base vidée et reconstruite à chaque démarrage -- aucune donnée
        # saisie par un visiteur n'y survit (voir db.py::
        # reinitialiser_donnees_demo), puis réensemencée avec le dossier
        # fictif de démonstration.
        db.reinitialiser_donnees_demo()
        _ensemencer_dossier_demo()
    else:
        db.init_db()  # crée/complète le schéma SQLite si besoin, comme main() dans gui.py
        if demo.mode_demo_serveur():
            # DEMO_RESET_DB=false : mode démo actif (réponses cannées,
            # bandeau...) mais base existante préservée -- on ajoute
            # seulement le dossier de démo s'il manque, sans rien effacer.
            _ensemencer_dossier_demo()
    yield


app = FastAPI(
    title="Plaid'IA API",
    description="API REST + streaming SSE exposant les fonctionnalités de Plaid'IA (analyse.py, db.py, "
    "recherche_juridique.py, judilibre.py, extract.py, export.py) pour un front web séparé.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS -------------------------------------------------------------------
# Origines autorisées configurables via CORS_ORIGINS (liste séparée par des
# virgules) — défaut couvrant les ports par défaut de Vite et Create-React-App
# pour le développement local du futur front séparé.
origines = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origines.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Protection anti-abus : débit par IP (slowapi) --------------------------
# Limite globale simple appliquée à toutes les routes via SlowAPIMiddleware
# (pas besoin de décorer chaque route individuellement) -- configurable via
# RATE_LIMIT_DEFAUT (ex. "120/minute") pour un déploiement particulier.
limiter = Limiter(key_func=get_remote_address, default_limits=[os.environ.get("RATE_LIMIT_DEFAUT", "60/minute")])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def limite_debit_handler(request: Request, exc: RateLimitExceeded):
    # SlowAPIMiddleware appelle ce handler de façon SYNCHRONE (voir
    # slowapi/middleware.py::sync_check_limits) : un `async def` ici serait
    # silencieusement ignoré au profit du message par défaut de slowapi
    # ("Rate limit exceeded: ..."), d'où ce handler volontairement sync.
    return JSONResponse(status_code=429, content={"detail": "Trop de requêtes depuis cette adresse — merci de patienter avant de réessayer."})


# --- Clé API personnelle ("Utiliser ma propre clé Anthropic") ---------------
# Un visiteur peut fournir sa propre clé via l'en-tête X-Anthropic-Api-Key
# (jamais dans le corps ni dans l'URL, jamais journalisée) -- posée pour la
# durée de la requête via un ContextVar dans analyse.py, lu en priorité par
# _client(). Voir demo.py::mode_demo_effectif : une clé personnelle fait
# sortir CETTE requête du mode démo, sans rien changer pour les autres
# visiteurs ni pour l'état structurel du serveur.
EN_TETE_CLE_API = "x-anthropic-api-key"


@app.middleware("http")
async def cle_api_personnelle_middleware(request: Request, call_next):
    cle = request.headers.get(EN_TETE_CLE_API)
    jeton = legacy_analyse.definir_cle_api_requete(cle.strip() if cle else None)
    try:
        return await call_next(request)
    finally:
        legacy_analyse.reinitialiser_cle_api_requete(jeton)


# --- Langue de sortie (internationalisation FR/EN) --------------------------
# Le sélecteur de langue de la barre de tâches (frontend/src/i18n) envoie
# l'en-tête X-Langue avec CHAQUE appel (voir frontend/src/api/http.ts) --
# posée pour la durée de la requête via le même idiome de ContextVar que la
# clé API personnelle ci-dessus, lue par analyse._directive_langue() dans
# tous les prompts système qui produisent du texte pour l'utilisateur final.
EN_TETE_LANGUE = "x-langue"


@app.middleware("http")
async def langue_requete_middleware(request: Request, call_next):
    langue = request.headers.get(EN_TETE_LANGUE)
    jeton = legacy_analyse.definir_langue_requete(langue.strip() if langue else None)
    try:
        return await call_next(request)
    finally:
        legacy_analyse.reinitialiser_langue_requete(jeton)


# --- Gestion d'erreurs uniforme -----------------------------------------
# Toutes les fonctions métier réutilisées (analyse.py, judilibre.py,
# legifrance.py, extract.py...) lèvent des exceptions Python standard —
# jamais des HTTPException FastAPI, puisqu'elles ne connaissent rien du web.
# On les traduit ici en JSON {"detail": "..."} exploitable côté front, sans
# jamais laisser passer une trace Python brute.

@app.exception_handler(EnvironmentError)
async def env_error_handler(request, exc: EnvironmentError):
    # Clé API / identifiants manquants (ANTHROPIC_API_KEY, JUDILIBRE_KEY_ID,
    # LEGIFRANCE_CLIENT_ID/SECRET...) — erreur de configuration serveur.
    return JSONResponse(status_code=500, content={"detail": f"Erreur de configuration serveur : {exc}"})


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    # Typiquement : le modèle a répondu dans un format non-JSON inattendu
    # (analyse.py lève ValueError dans ce cas précis).
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc: FileNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(legacy_extract.DocumentNumeriseError)
async def document_numerise_handler(request, exc: legacy_extract.DocumentNumeriseError):
    # PDF sans couche de texte exploitable (scan) -- voir extract.py §8.
    # 422 : le fichier est valide, c'est son contenu qui n'est pas exploitable.
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(DemandeRefusee)
async def demande_refusee_handler(request, exc: DemandeRefusee):
    # Garde-fou d'entrée (sécurité, voir security_guard.py et
    # ARCHITECTURE_MULTI_AGENTS.md §1) -- la demande n'a jamais atteint
    # l'agent principal. 422 : la requête est valide, c'est son contenu qui
    # est refusé.
    return JSONResponse(status_code=422, content={"detail": exc.reason})


@app.exception_handler(ImportError)
async def import_error_handler(request, exc: ImportError):
    # Dépendance optionnelle manquante (pdfplumber, python-docx, reportlab,
    # openpyxl...) — erreur de configuration serveur, pas une erreur cliente.
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request, exc: Exception):
    # Filet de sécurité final : jamais de trace Python brute renvoyée au front.
    return JSONResponse(status_code=500, content={"detail": f"Erreur interne : {exc}"})


# --- Routers ------------------------------------------------------------
app.include_router(dossiers.router)
app.include_router(analyse.router)
app.include_router(jurisprudence.router)
app.include_router(notes.router)
app.include_router(greffier.router)
app.include_router(chat.router)
app.include_router(intention.router)
app.include_router(epingles.router)
app.include_router(versions.router)
app.include_router(documents.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "service": "plaidia-api"}


@app.get("/api/config", tags=["health"])
def config():
    """Consommé par le front au démarrage pour afficher le bandeau "Mode
    démo" (voir useAppStore::chargerConfiguration). Reflète l'état
    structurel du serveur -- pas l'effet d'une éventuelle clé personnelle
    que CE visiteur fournirait ensuite pour ses propres requêtes."""
    return {
        "demo_mode": demo.mode_demo_serveur(),
        "max_texte_caracteres": demo.MAX_TEXTE_CARACTERES,
        "dossier_demo_nom": demo_data.NOM_DOSSIER_DEMO if demo.mode_demo_serveur() else None,
    }
