# Dockerfile du backend Plaid'IA (FastAPI).
#
# IMPORTANT : le contexte de build doit être la RACINE du dépôt, pas
# backend/ -- l'API réutilise telle quelle une poignée de modules Python
# qui vivent à la racine (analyse.py, db.py...), voir app/bootstrap.py.
#
#   docker build -f backend/Dockerfile -t plaidia-api .
#
# render.yaml et railway.json (racine du dépôt) sont déjà configurés avec
# le bon contexte -- rien à faire de plus sur ces plateformes.

FROM python:3.11-slim

WORKDIR /app

# Dépendances Python -- copiées avant le reste du code pour profiter du
# cache Docker (un `pip install` ne se relance que si requirements.txt change).
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Modules métier réutilisés tels quels (racine du projet) -- copiés un par
# un, JAMAIS un `COPY . .` qui embarquerait apikey.txt ou les fichiers
# doublons ("- Copie") qui traînent au dépôt (voir .dockerignore, qui les
# exclut de toute façon, mais on ne compte pas sur une seule protection).
COPY analyse.py db.py recherche_juridique.py judilibre.py extract.py export.py legifrance.py paths.py ./

# API FastAPI
COPY backend/app ./backend/app

WORKDIR /app/backend

# Render/Railway injectent PORT à l'exécution ; 8000 est le repli en local
# (`docker run -p 8000:8000 plaidia-api`, sans -e PORT).
ENV PORT=8000
EXPOSE 8000

# Forme shell (pas la forme exec) pour que ${PORT} soit interpolé par le
# shell au démarrage du conteneur -- Render fixe PORT à une valeur
# différente de 8000 à chaque déploiement.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
