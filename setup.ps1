$ErrorActionPreference = "Stop"

py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm ci
npm ci --prefix frontend
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
$env:PYTHONPATH = "backend"
& .\.venv\Scripts\alembic.exe -c backend\alembic.ini upgrade head
Write-Output "Setup complete. Activate the venv, configure .env, then run npm run dev."
