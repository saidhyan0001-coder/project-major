# Testing and verification

## Commands

Activate `.venv` first on Windows, or use `source .venv/bin/activate` on Linux:

```bash
export PYTHONPATH=backend
pytest backend/tests -q
npm --prefix frontend run test -- --run
npm --prefix frontend run build
alembic -c backend/alembic.ini upgrade head
```

On PowerShell, use `$env:PYTHONPATH='backend'` before pytest. Root `npm run test` is a Windows-oriented convenience command.

## Automated coverage

- Server catalog pricing, pending order state, private tracking token, explicit confirmation.
- Tracking rejection without valid bearer token.
- Prompt-injection block and raw-input non-storage.
- Benign exact-menu voice/chat order proposal and explicit-only confirmation.
- Staff authentication and confirmed -> preparing -> ready status flow.
- AprilTag reporter auth, unknown registry, correct mapping, wrong ID and low-margin behavior.
- Health/readiness and explicit missing-Gemini configuration failure.
- Frontend menu loading, guest order form, API confirmation before success UI.

## Manual checks for release

1. Run backend and verify `/api/v1/health` and `/api/v1/ready`.
2. Create an order from the UI; confirm the one-time token; refresh and query with token; try a wrong token.
3. Try changing price in a manual request; verify server totals still use the catalog.
4. Configure Gemini and test valid responses, timeout/quota, unavailable model and missing key. Do not treat mock-provider tests as proof of Gemini availability.
5. Verify mic permission allowed/denied, unsupported browser, retry/stop, transcript disclosure, browser speech output.
6. Configure actual AprilTag mapping and run detector against correct tag, wrong tag, unknown tag, poor light, low margin, disconnected API. Physical Pi/camera tests are not covered by mocked API tests.
7. Confirm staff login and state controls. Ensure unauthorized guest cannot enumerate orders/events.
8. For release, test production CORS, HTTPS, PostgreSQL migration/restore, rate limiter, secret rotation, Vercel/backend integration and monitoring.

Record environment/hardware and actual command outputs in `FINAL_VERIFICATION_REPORT.md`.
