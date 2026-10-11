# Final verification report

## Completed checks

| Area | Result | Evidence |
|---|---|---|
| Backend API | PASS | `PYTHONPATH=backend .venv/Scripts/pytest.exe backend/tests -q` — 8 passed |
| Frontend tests | PASS | `npm run test -- --run` — 2 passed |
| Frontend production build | PASS | `npm run build` — TypeScript and Vite build succeeded |
| Frontend dependency audit | PASS | `npm audit` — 0 vulnerabilities |
| Backend dependency audit | PASS | `pip-audit -r backend/requirements.txt` — no known vulnerabilities |
| Git whitespace check | PASS | `git diff --check` |
| Local API | PASS | `http://127.0.0.1:8011/api/v1/health` returned `{"status":"ok","service":"hotel-ordering-api"}` |
| Vercel deployment | PASS, preview only | Production deployment `project-major-tau.vercel.app`; website and menu loaded after deploying with a temporary `/tmp` SQLite path |
| Live Vercel API | PASS, preview only | `/api/v1/health` and `/api/v1/menu` both returned HTTP 200 |
| Live Vercel order preview | PASS | Server-priced Fruit plate preview returned $9.50 without creating an order |
| Live Vercel assistant | PASS, mock provider | Menu question returned a valid menu response; no Gemini key was configured or sent |
| Browser order workflow | PASS | Menu loaded, item added, server-priced order confirmed, then private-token tracking verified after reload |
| Assistant workflow | PASS | Chat generated an unplaced draft; entering guest details later and explicitly confirming successfully placed the order |
| Database migration | PASS, limited | Alembic upgrade succeeded against a fresh SQLite database |

The backend test run reports an upstream Starlette `httpx`-based `TestClient` deprecation warning; it does not fail the suite.

GitHub reported 2 moderate Dependabot alerts after the push. The repository's Dependabot details page was unavailable in this session, while local `npm audit` and `pip-audit` checks (including the optional camera requirements) found no known vulnerabilities. Review the GitHub Security tab before production release to identify and resolve those remaining alerts.

## Blocked or not run

- **Production order storage: BLOCKED.** The hosted backend currently writes to temporary `/tmp` SQLite storage, which is not durable across serverless instances or redeployments. Configure PostgreSQL and migrate before accepting real orders.
- **Live Gemini request: NOT CONFIGURED.** The hosted preview intentionally uses the mock provider; no `GEMINI_API_KEY` was configured or sent. A real Gemini model response was not tested.
- **Physical AprilTag camera test: NOT RUN.** No Raspberry Pi/camera device is available. The helper compiles, but detector installation and real tag capture/reporting remain to be checked on the target hardware.
- **Browser microphone capture: NOT RUN.** The text assistant and browser voice controls are implemented, but this verification environment did not grant a physical microphone/speech-service test.
- **Migration against historical user data: NOT RUN.** Only a fresh database was used; the existing historical database was not modified.

The public preview is available at [https://project-major-tau.vercel.app](https://project-major-tau.vercel.app). It is a working UI/API preview using the deterministic mock assistant, not a production hotel ordering system. Do not accept real orders until persistent database storage and operational credentials are configured.
