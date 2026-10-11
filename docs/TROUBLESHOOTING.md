# Troubleshooting

## `npm run dev` cannot find Python packages

Activate `.venv` in the same PowerShell/session or use the explicit venv executable. Reinstall `python -m pip install -r backend/requirements.txt`, then run `npm run db:migrate`.

## API reports database unavailable or locked

Check `DATABASE_URL`, database file permissions, and that the parent directory is writable. SQLite allows a simple single-instance demo, not multi-worker production. For deployment use PostgreSQL, run migrations once, and ensure the app connection URL is private.

## Menu is empty / schema mismatch

Run Alembic migration from the repo root with `PYTHONPATH=backend`. App startup seeds the development menu only when the catalog has no rows. Production menu authoring/sync is not provided.

## Gemini returns 503

Check backend logs for `gemini_request_failed` (they omit guest prompt and secrets), set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, and `GEMINI_MODEL` on the backend, and verify that the model is enabled for the API key/quota. Do not place keys in frontend/Vercel public variables. Mock provider is a separate explicit mode, not a fallback.

## Voice/microphone is unavailable

Use a supported browser and HTTPS or localhost, grant microphone permission, then try again. If speech recognition is not implemented by that browser or permission is denied, type in chat. Browser speech service/audio handling follows that browser/vendor; the app does not claim local-only audio processing.

## Staff access denied

Set `STAFF_API_TOKEN` as a backend secret, restart backend, and enter exactly that token in the staff panel. Production should migrate to identity-aware SSO rather than a shared secret.

## AprilTag can't open camera or never verifies

Install `apriltag-requirements.txt` in a compatible camera environment; check device index/permissions, lighting, tag size/family, camera focus, and API connectivity. Configure reporter secret on both server and camera client. Register the **actual** family/ID per room and floor using staff access. Wrong/unmapped tag or margin <35 correctly does not verify. No room coordinates are used.

## Vercel page loads but API calls fail

Set public `VITE_API_BASE_URL` at Vercel build time, redeploy, serve API with valid HTTPS, configure the exact frontend domain in backend `CORS_ORIGINS`, and check backend health. CORS does not provide authentication; guest tracking/staff tokens remain independently enforced.

## Credential exposure

Immediately revoke or rotate the Gemini/API/staff/camera secret in its provider and all deployment environments, inspect access logs, invalidate old staff/camera tokens, and rebuild/redeploy. Never add `.env` to Git.
