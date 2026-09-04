# Makefile — alternative à `npm run dev` pour qui a `make` sous la main
# (macOS/Linux natif, ou Windows via WSL/Git Bash/choco install make).
# Suppose que le venv backend est déjà créé + activé, et que
# `npm install` a déjà été lancé dans frontend/ — voir README.md,
# section "Installation locale", pour la mise en place initiale.

.PHONY: dev dev-backend dev-frontend test test-backend test-frontend install

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Lance backend (:8000) et frontend (:5173) ensemble -- Ctrl+C arrête les deux."
	@( trap 'kill 0' EXIT; \
	   (cd backend && python -m uvicorn app.main:app --reload --port 8000) & \
	   (cd frontend && npm run dev) & \
	   wait )

dev-backend:
	cd backend && python -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest
	cd frontend && npm test

test-backend:
	cd backend && python -m pytest

test-frontend:
	cd frontend && npm test
