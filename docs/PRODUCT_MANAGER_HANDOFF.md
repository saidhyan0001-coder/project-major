# Product manager handoff

## Product scope

The deliverable is hotel guest room-service ordering with a website, backend/database, optional Gemini conversational assistance, browser voice, NLP abuse screening, staff order updates, and optional AprilTag camera observation. It does **not** include telephone calling, ROS 2, robot navigation, robot task dispatch, hotel PMS integration, payments, or real kitchen/menu synchronization.

## Start a local demo

1. Follow the repository README setup steps and configure `.env`.
2. Set `LLM_PROVIDER=mock` to demo offline or configure a valid Gemini API key/model and set `LLM_PROVIDER=gemini`.
3. Set distinct random values for `STAFF_API_TOKEN` and `APRILTAG_REPORT_TOKEN`.
4. Run database migration and app; open the local website.
5. Add an item, enter a test guest and room, submit the order, and retain the displayed one-time tracking token.
6. Use the staff token in Staff access to transition the confirmed order to preparing and ready.
7. To demonstrate the assistant, ask for an exact menu name. Review the draft and press Confirm this order.
8. For camera verification, install optional dependencies, register real tag-to-room mapping, and use the Pi/camera instructions.

## Ownership and operations checklist

- Product owner: approve menu, taxes/fees, allergen wording, guest authentication and retention policy.
- Hotel operations: provide a maintained menu/availability process, authorize staff access, validate state transitions and cancellation policy.
- IT/security: provision HTTPS API/database hosting; use a managed secret store; configure exact CORS; replace shared token with hotel SSO/roles; establish rate limits, logging, monitoring, backups, incident process.
- AI owner: select a model supported by configured API credentials; review prompt-safety monitoring, latency, quota/cost, data processing terms, and retention.
- Voice owner: approve browser vendor audio handling, required browsers/languages, accessibility and fallback; phone integration is a separate project.
- Camera owner: provide Pi model/OS, camera, printed tag family/IDs and verified room/floor registry; perform lighting/distance testing. This is not robot navigation.
- Deployment owner: supply Vercel project access and public HTTPS API URL; deploy/check frontend and backend independently.

## Credentials and secrets

Credentials are never committed. Gemini key, staff token, and camera reporter token belong only in backend deployment secrets. `VITE_API_BASE_URL` is public by design. If a key is pasted into source, logs, or a chat, revoke/rotate it before deployment.

## Acceptance criteria

- The public site only reports an order after successful backend creation and confirmation.
- Client prices cannot override catalog pricing.
- A guest without a matching private token cannot access an order.
- Staff endpoints reject requests without the server token.
- Model-injected item names do not create unknown/unavailable menu items.
- Injection attempts generate safe blocked responses and metadata-only flags.
- AprilTag mismatches and low confidence remain unverified.
- Gemini and camera behavior are reported as blocked until real key/hardware execution.

## Remaining project decisions

Select a real hotel brand/menu, production identity model, taxes/gratuity, authorization rules, order retention, supported spoken locales, Gemini model, PostgreSQL host, API host, Vercel project/URL, and actual room-to-tag mapping. These are operational/product decisions and should not be guessed in code.
