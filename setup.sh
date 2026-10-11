#!/usr/bin/env bash
set -euo pipefail

python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
npm ci
npm ci --prefix frontend
if [ ! -f .env ]; then
  cp .env.example .env
fi
export PYTHONPATH=backend
alembic -c backend/alembic.ini upgrade head
printf '\nSetup complete. Activate the venv, configure .env, then run npm run dev.\n'
