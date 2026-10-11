# Final verification report

## Completed checks

| Area | Result | Evidence |
|---|---|---|
| Backend API | PASS | `PYTHONPATH=backend .venv/Scripts/pytest.exe backend/tests -q` — 8 passed |
| Frontend tests | PASS | `npm run test -- --run` — 2 passed |
| Frontend production build | PASS | `npm run build` — TypeScript and Vite build succeeded |
| Frontend dependency audit | PASS | `npm audit` — 0 vulnerabilities |
| Git whitespace check | PASS | `git diff --check` |
| Local API | PASS | `http://127.0.0.1:8011/api/v1/health` returned `{"status":"ok","service":"hotel-ordering-api"}` |
| Browser order workflow | PASS | Menu loaded, item added, server-priced order confirmed, then private-token tracking verified after reload |
| Assistant workflow | PASS | Chat generated an unplaced draft; entering guest details later and explicitly confirming successfully placed the order |
| Database migration | PASS, limited | Alembic upgrade succeeded against a fresh SQLite database |

The Python test run reports one upstream Starlette/AnyIO deprecation warning; it does not fail the suite.

## Blocked or not run

- **Hosted Vercel deployment: BLOCKED.** No Vercel token/account authorization is configured. The backend also needs separate HTTPS hosting and its own deployment configuration.
- **Live Gemini request: BLOCKED.** No `GEMINI_API_KEY` is configured. Mock-provider interactions and the missing-credential error path were tested; a real model response was not.
- **Physical AprilTag camera test: NOT RUN.** No Raspberry Pi/camera device is available. The helper compiles, but detector installation and real tag capture/reporting remain to be checked on the target hardware.
- **Browser microphone capture: NOT RUN.** The text assistant and browser voice controls are implemented, but this verification environment did not grant a physical microphone/speech-service test.
- **Migration against historical user data: NOT RUN.** Only a fresh database was used; the existing historical database was not modified.

The website and API used for browser checks are local development servers, not a public production deployment. Do not treat the project as publicly live until the blocked hosting, credentials, and device steps are completed.
