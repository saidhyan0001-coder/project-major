# Vercel deployment

The repository root `vercel.json` configures Vercel Services to deploy the Vite frontend and FastAPI backend together. The frontend uses same-origin `/api/v1/...` requests in production; local development continues to use `http://localhost:8000`.

## Configure

1. Import `saidhyan0001-coder/project-major` in Vercel and select the detected multi-service project.
2. Use the repository root `vercel.json` service definitions and deploy.
3. The app runs without a Gemini key using its explicit mock provider. To enable Gemini later, set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, and an available `GEMINI_MODEL` as backend-only secrets.
4. Before real orders, configure a persistent PostgreSQL database and apply Alembic migrations. Do not use the default SQLite database for production on serverless infrastructure; instance-local files are not durable.
5. Set strong backend-only `STAFF_API_TOKEN` and `APRILTAG_REPORT_TOKEN` secrets before enabling staff or camera features.
6. Test the deployed `/api/v1/health`, menu, guest order, and private-token tracking workflows before sharing the app.

## Important

- No Gemini, staff, or camera credentials are required to deploy the public guest UI and mock assistant. Until a Gemini key is configured, this is not a Gemini-backed assistant.
- The default SQLite storage is suitable for local development only. A Vercel deployment using SQLite must be treated as a non-production preview: data can be lost across function instances/redeployments.
- Do not set any API key or staff/camera token as a `VITE_*` variable.
- HTTPS is required for microphone APIs in production; localhost is also treated as a secure context for development.
