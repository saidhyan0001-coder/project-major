#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
if [ -f .venv/Scripts/activate ]; then
  . .venv/Scripts/activate
elif [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
fi

pip install --upgrade pip
pip install -r backend/requirements.txt
npm install --prefix frontend
python -m app.db init-db || true
printf '\nSetup complete. Run: npm run dev\n'
