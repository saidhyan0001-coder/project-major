# Implementation record

## Completed locally

- Audited the existing prototype and switched the product scope from robot-delivery mockup to guest hotel ordering/assistant.
- Added a server-owned catalog, price preview, order creation, explicit confirmation, hash-only private tracking credentials, cancellation, state validation, and authenticated staff APIs.
- Added text conversation, deterministic attack screening, metadata-only security events, explicit mock provider and Google Gen AI Gemini provider with structured response checks and bounded retry.
- Added browser speech recognition and speech synthesis controls with permission/provider limits explained.
- Added AprilTag room/floor mappings and authenticated observation API with exact tag-family/id and confidence validation, plus standalone OpenCV camera helper.
- Added Alembic baseline/legacy schema adaptation, backend/frontend tests, Vercel project config and Pi/deployment/handoff documents.

## Remaining operational work

- Apply actual hotel menu, brand, identity and retention policies.
- Supply valid Gemini model/key and production backend secrets.
- Select a PostgreSQL/API hosting provider and run backup/restore/monitoring checks.
- Verify optional camera integration with real Pi/camera/printed markers.
- Connect repository to Vercel with owner permissions and deploy frontend against live HTTPS backend.
- Replace shared staff token and in-process rate limiter with production identity/gateway controls.

The executed commands and evidence statuses are in `FINAL_VERIFICATION_REPORT.md`.
