# The Willow — Hotel Ordering Assistant

Guest-facing hotel room-service ordering with a React + TypeScript website, FastAPI API, persistent SQLAlchemy database, guarded Gemini conversation service, browser speech controls, and optional camera-based AprilTag room verification. **There is no ROS 2, Nav2, robot navigation, or robot task dispatch in this project.**

## Current implementation and honest limits

- The local mock conversation provider supports menu questions and exact menu-name order drafts. It is for development/tests, not an LLM.
- Gemini calls are made only by the backend when `LLM_PROVIDER=gemini`; model ID and key are server configuration. A missing key/model yields an explicit API error, never a pretend AI answer.
- Browser voice uses the browser's Web Speech recognition/synthesis capability where supported. It is not a telephone integration, and browser speech services may process audio according to browser/vendor policies.
- AprilTag detection is an optional separate OpenCV + `pupil-apriltags` camera helper, based on the sample approach linked in [the user-provided repository](https://github.com/saidhyan0001-coder/aprila-tag). Camera hardware was not available for validation in this environment. A recorded API observation is matched against a staff-configured room/floor/tag registry. It does not control a robot.
- Public Vercel preview: [project-major-tau.vercel.app](https://project-major-tau.vercel.app). The frontend and API are deployed together and use the mock assistant without requiring a Gemini key.
- The Vercel preview currently uses SQLite under `/tmp`, which is temporary serverless storage. Do not use it for real guest orders; data is not durable. Configure PostgreSQL and run migrations before production use.
- Gemini, Raspberry Pi camera, phone calls, and hotel identity/PMS integrations require external credentials/hardware and are not active in the hosted preview.

## Requirements

- Python 3.11
- Node.js 20.19+ or 22.12+
- npm 10+
- Optional camera: USB camera, OpenCV-compatible operating system, and the packages in `apriltag-requirements.txt`
- Optional Gemini: Google Gen AI API key and a model identifier available to that key

## Local setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
npm ci
npm ci --prefix frontend
Copy-Item .env.example .env
```

Edit `.env`:

- Keep `LLM_PROVIDER=mock` for offline development/tests, or configure both `GEMINI_API_KEY` and `GEMINI_MODEL`, then set `LLM_PROVIDER=gemini`.
- Set long random values for `STAFF_API_TOKEN` and `APRILTAG_REPORT_TOKEN` if using staff or camera reporting.
- `VITE_API_BASE_URL` is only the public backend base URL; never place secrets in a `VITE_*` variable.

Initialize/migrate the database and start the app:

```powershell
npm run db:migrate
npm run dev
```

- Website: http://localhost:5173
- API health: http://localhost:8000/api/v1/health
- Readiness: http://localhost:8000/api/v1/ready
- OpenAPI docs: http://localhost:8000/docs

Python virtual environment should remain active so the `python`, `pytest`, `alembic`, and `uvicorn` commands use project dependencies.

## Common commands

- `npm run dev` — run frontend and backend in development
- `npm run backend` — backend only
- `npm run frontend` — frontend only
- `npm run db:migrate` — apply Alembic migrations
- `npm run test` — backend and frontend tests (Windows)
- `npm run lint` — backend bytecode compile and frontend type-check/production build
- `npm run health` — check backend health (curl must be installed)

On Linux/Raspberry Pi, see [Raspberry Pi Deployment](docs/RASPBERRY_PI_DEPLOYMENT.md) for venv activation and native commands.

## Guest ordering

1. Browse the server-provided menu and add items.
2. Enter guest name and room number; review the displayed cart.
3. Choose “Review & confirm order”. Backend reprices from its menu, persists a pending order and issues a random private tracking token; the website explicitly confirms that order with the token.
4. Save order number and private tracking token to retrieve status. Only the token holder can retrieve/cancel that individual order.
5. Staff authenticate with `STAFF_API_TOKEN`, move confirmed orders to preparing/ready, and can inspect security and AprilTag events.

The price sent by the browser is never accepted as authoritative. Menu item IDs and quantities are revalidated server-side.

## Gemini and voice

The browser sends text to the backend conversation route. The backend rejects common injection/data-exfiltration/price-tampering patterns, constructs a prompt from trusted menu data, requests constrained JSON from the configured Gemini model, and validates each proposed menu item against the live catalog. Any order still requires the guest to press the explicit confirmation button. See [Architecture](docs/ARCHITECTURE.md) and [Troubleshooting](docs/TROUBLESHOOTING.md).

Voice is browser voice only: browser speech recognition transcribes the user's audio; the transcript follows the same backend conversation and validation path as typed chat; speech synthesis reads the answer. Unsupported browser, denied mic, network, and AI errors are shown. No audio recordings or raw conversation transcript are persisted by this API.

## AprilTag verification (optional)

The sample repository link points to a Git submodule for a Python detection sample using OpenCV and `pupil-apriltags`. The integrated optional client uses those packages to detect tags from an actual camera frame and submit a tag family, ID, and decision margin to the API. Staff must first register the real tag for the room/floor—tag IDs do not equal room numbers.

1. Configure `APRILTAG_REPORT_TOKEN` in the backend and camera environment.
2. Configure `STAFF_API_TOKEN`, sign in to the staff portal, and register a room, floor, family, and **measured** tag ID.
3. Install camera dependencies: `python -m pip install -r apriltag-requirements.txt`.
4. Run from the repository root, replacing room/floor values with the real destination:

```powershell
$env:APRILTAG_REPORT_TOKEN = "your-camera-report-token"
python tools\apriltag_camera.py --room 204 --floor 2 --device 0 --api-url http://127.0.0.1:8000
```

The API only returns `verified: true` when an authenticated camera report matches the registered room, floor, family, tag ID, and minimum decision margin (35). Unknown mappings, wrong tags, low confidence, missing camera, and API timeouts are not success. See [the camera helper](tools/apriltag_camera.py) and [AprilTag handoff notes](docs/RASPBERRY_PI_DEPLOYMENT.md).

## Security/deployment notes

- Do not commit `.env` or real API tokens. If exposed, revoke/rotate them immediately.
- Staff access uses one shared backend bearer token for this prototype; production should use hotel SSO/individual staff identities, roles, audit retention, HTTPS, and a secrets manager.
- Order tracking tokens are returned only at order creation and only their SHA-256 hashes are stored.
- Do not enable wildcard CORS in production. Configure `CORS_ORIGINS` to the deployed website origin.
- Process-local API throttling is a development safety net; use a gateway/distributed rate limiter in production.
- SQLite is for local setup. Production should use PostgreSQL and managed encrypted backups.
- Vercel hosts the static website only. Deploy the API and database separately; set Vercel's `VITE_API_BASE_URL` to the public HTTPS API base URL. See [Vercel deployment](docs/VERCEL_DEPLOYMENT.md).

## Project manager handoff

Start with [the product manager handoff](docs/PRODUCT_MANAGER_HANDOFF.md), [the API contract](docs/API_CONTRACT.md), [testing guide](docs/TESTING.md), and [the final verification report](docs/FINAL_VERIFICATION_REPORT.md).

## API overview

All application routes use `/api/v1`. Menu, order, conversation, staff, readiness, and AprilTag endpoints are documented in [docs/API_CONTRACT.md](docs/API_CONTRACT.md). Interactive OpenAPI is at `/docs` while the backend is running.
