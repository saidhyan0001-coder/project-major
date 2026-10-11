# Vercel frontend deployment

Vercel deployment is **not performed by this repository configuration alone**. It requires the owner to connect the GitHub repository and provide Vercel account/project permissions, plus a separately hosted HTTPS API.

## Configure

1. Deploy FastAPI and PostgreSQL on a supported backend provider first. Apply Alembic migrations before accepting requests.
2. In Vercel, import `saidhyan0001-coder/project-major` and set the project **Root Directory** to `frontend`.
3. `frontend/vercel.json` declares Vite build and `dist` output.
4. Set Vercel build environment variable `VITE_API_BASE_URL=https://<your-api-host>` (public URL only, no trailing slash recommended).
5. On backend host set `CORS_ORIGINS=https://<your-vercel-domain>` and production secrets: `GEMINI_API_KEY`, `GEMINI_MODEL`, `STAFF_API_TOKEN`, `APRILTAG_REPORT_TOKEN`, `DATABASE_URL`, `APP_ENV=production`, `LLM_PROVIDER=gemini`.
6. Confirm browser requests reach HTTPS API and no secrets appear in built frontend assets, logs, or browser requests.
7. Deploy preview first; run manual guest/staff, security, voice, and error checks; then promote production.

## Important

- Do not set any API key or staff/camera token as a Vercel `VITE_*` variable.
- A deployed frontend without a deployed API is not an operational app.
- HTTPS is required for microphone APIs in production; localhost is also treated as a secure context for development.
- Set permitted origins explicitly; do not use wildcard CORS.
- Configure Vercel environment variables separately for Preview and Production as needed.
- No Vercel token/domain/production deployment URL was present during this work, so deployment status must remain `BLOCKED` until someone with account access performs it.
