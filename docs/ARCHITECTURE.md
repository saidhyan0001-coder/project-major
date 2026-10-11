# Architecture and data flow

## Scope

The app covers hotel menu browsing, guest room-service orders, staff order management, chat/voice assistance, abuse detection, and optional AprilTag camera room checks. It does not implement telephony, ROS 2, Nav2, motor control, or robot task dispatch.

## Components

- **Vite/React website:** menu, cart, order placement/confirmation, private token-based status lookup, chat, browser speech controls, and token-protected staff panel.
- **FastAPI:** validates requests, derives totals from the catalog, handles guest tracking tokens and staff authorization, screens untrusted assistant input, calls Gemini on the server, checks model item names against available menu records, and stores state.
- **SQLAlchemy:** persistence for catalog, orders/line items, conversations/draft proposals, privacy-preserving security events, AprilTag room mappings/observations, and audit events.
- **Gemini service:** Google Gen AI SDK, backend API key, configured model, constrained JSON output, and bounded retry. `mock` provider is explicit and offline; it is never substituted after a Gemini failure.
- **Browser voice:** Web Speech `SpeechRecognition` (or webkit-prefixed implementation) and browser `speechSynthesis`; browser/vendor audio processing applies. Text conversation uses the same backend endpoint.
- **Optional Pi camera utility:** OpenCV captures frames, `pupil-apriltags` detects a configured family, helper submits ID + decision margin over HTTPS, API matches an administrator-registered room/floor mapping. No images are uploaded or retained by this helper.

## Guest order sequence

1. Website requests `GET /api/v1/menu`.
2. Guest adds catalog IDs/quantities, enters name/room, reviews the cart.
3. Website asks `POST /api/v1/orders/preview`; API looks up prices and availability itself.
4. On the guest's explicit “Review & confirm order” submit, API persists a pending order and returns its ID and a random tracking token once.
5. Website explicitly calls `POST /api/v1/orders/{id}/confirm` with that token. Only a successful API response appears as confirmed.
6. Backend persists only a hash of the token; subsequent status checks require the raw token and matching ID. No public list of guest orders exists.
7. Authorized staff use the API bearer secret to see incoming orders and transition confirmed -> preparing -> ready or cancel permitted states.

## Assistant sequence and trust boundaries

Browser transcript/text -> rate limit -> deterministic injection/privacy/price-tampering screening -> trusted available menu context -> configured Gemini or explicitly selected local mock -> JSON parsing and intent validation -> exact menu-name/quantity whitelist -> website displays proposed draft -> guest confirms explicitly -> order API validates again and persists.

The model has no database connection, shell access, browser credentials, arbitrary tool execution, or authority to set prices, availability, permissions, or order states. Security event records contain a category, severity, session identifier, and SHA-256 fingerprint, not the raw prompt. Normal voice transcripts are not stored by the backend.

## AprilTag trust boundary

A tag ID is not a room number. Staff registers `(room_number, floor_id) -> (family, id)` based on the actual installed printed marker. The camera reporter has a separate bearer token. API verification requires the expected configured location, exact family and ID, and decision margin >= 35. Unknown mapping, mismatch, or low confidence is recorded as not verified. This is a standalone room-marker verification facility only; it does not trigger robot movement or mark an order delivered.

## Deployment boundary

Vercel serves the static frontend. FastAPI and PostgreSQL belong on a backend host reachable over HTTPS. Browser has only a public backend base URL; `GEMINI_API_KEY`, staff token, and camera token remain backend secrets. Set exact Vercel origin(s) in backend `CORS_ORIGINS`.

## Current limitations

- The sample menu is seeded during app startup; production menu management/PMS sync is not implemented.
- `STAFF_API_TOKEN` is a single shared prototype credential; production should use SSO/individual staff roles.
- Rate limiting is in-process and does not replace a production API gateway.
- No telephone calls or server-side paid STT/TTS provider is configured.
- Physical camera/Pi, production PostgreSQL, live Gemini key, and Vercel deployment require external access and are not represented as verified.
