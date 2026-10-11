# Repository audit

Audit performed against the checkout at commit `ef0a5f8` before the current hotel-assistant implementation changes.

| Component | Current implementation at audit | Missing work | Verification status |
|---|---|---|---|
| Frontend | React + TypeScript + Vite dashboard in `frontend/src/App.tsx`; manual item name/price form and robot/task panels | Guest menu/cart, server-priced preview, private order tracking, voice/chat, staff view | Verified; the previous UI was a prototype |
| Backend | FastAPI routes in `backend/app/main.py`; SQLAlchemy SQLite models | Versioned API, request-specific order authorization, staff auth, catalog price authority, AI conversation | Verified; unsafe public order listing and open staff actions needed replacement |
| Gemini LLM | None; voice endpoint returned deterministic canned responses | Official Google Gen AI client, configured model, schema validation, timeout/error behavior | Verified missing |
| Voice | No browser mic, STT, or TTS integration | Browser Web Speech input/output and clear consent/errors | Verified missing |
| NLP security | No malicious input detection | Deterministic attack screening, privacy-preserving event record, test coverage | Verified missing |
| Database | SQLAlchemy/SQLite, orders, delivery/robot/voice tables; no Alembic migration | Menu catalog, guest bearer-token hash, conversation/security/tag tables, schema migration | Partial |
| Raspberry Pi | No Pi setup/handoff | OS/runtime guidance and optional camera dependencies | Unknown until target hardware is supplied |
| Vercel | No deployment config | Vite static output config and deployment guide | Verified missing |
| AprilTag | A separate GitHub repo contains a Git submodule pointing at a Python camera detection sample | Optional camera script and configured room/floor mapping | Source inspected; physical camera operation unavailable |

## Relevant evidence and constraints

- The repo initially contained commit `ef0a5f8472fe6a72ae84f7d1f35b5e3bc081ee19`.
- Runtime files showed FastAPI, SQLAlchemy, React, TypeScript, Vite, and pytest/Vitest.
- No Gemini SDK, actual browser voice, authentication, AprilTag detector, Pi-specific setup, or Vercel config was present.
- The linked AprilTag repo root contains `AprilTag-Detection-Python-Sample` as a Git submodule. Its upstream English README documents OpenCV plus `pupil-apriltags`, default family `tag36h11`, and MIT licensing. No upstream source was copied verbatim; the camera helper follows the documented detector interface and links to the user-provided repo.
- No ROS packages or robot integration are part of this application. Legacy robot database tables may remain in existing SQLite files but are not exposed by the updated API.

See `FINAL_VERIFICATION_REPORT.md` for the implementation and test status after this audit.
