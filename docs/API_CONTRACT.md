# API contract

All JSON application routes use `/api/v1`. FastAPI OpenAPI docs are at `/docs`. API errors return a non-2xx status and a `detail`; the frontend surfaces that error. Health endpoints are public.

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/v1/health` | Public | Process liveness |
| GET | `/api/v1/ready` | Public | Check database connectivity |
| GET | `/api/v1/menu` | Public | List available catalog entries |
| POST | `/api/v1/orders/preview` | Public | Server price/availability preview |
| POST | `/api/v1/orders` | Guest | Create pending order; returns tracking token once |
| POST | `/api/v1/orders/{id}/confirm` | Per-order token | Explicit guest confirmation |
| POST | `/api/v1/orders/{id}/track` | Per-order token | Retrieve only that order |
| POST | `/api/v1/orders/{id}/cancel` | Per-order token | Cancel only if state permits |
| POST | `/api/v1/conversations` | Public | Create transient conversation draft |
| POST | `/api/v1/conversations/{session_id}/messages` | Session ID | NLP screening and assistant reply/draft |
| POST | `/api/v1/conversations/{session_id}/confirm` | Guest confirmation text | Explicitly place conversation draft; accepts guest name/room at confirmation |
| GET | `/api/v1/staff/orders` | `Bearer STAFF_API_TOKEN` | List latest 200 orders |
| PATCH | `/api/v1/staff/orders/{id}/status` | Staff bearer | Set preparing/ready/cancelled subject to state machine |
| GET | `/api/v1/staff/security-events` | Staff bearer | View flagged event metadata (no raw prompts) |
| GET | `/api/v1/staff/audit-events` | Staff bearer | View audit records |
| PUT | `/api/v1/staff/apriltag-mappings` | Staff bearer | Register actual room/floor to tag-family/tag-ID mapping |
| POST | `/api/v1/apriltag/observations` | `Bearer APRILTAG_REPORT_TOKEN` | Submit detected family, ID, and margin; only exact high-confidence match verifies |
| GET | `/api/v1/staff/apriltag-events` | Staff bearer | View recent observations |

## Order input example

```json
{
  "guest_name": "Taylor Guest",
  "room_number": "501",
  "notes": "Please include napkins",
  "items": [{"menu_item_id": 2, "quantity": 1}]
}
```

No price/name from this payload controls the charge. The server retrieves the current menu record and computes the total. Quantity is limited to 1..20. The create response includes `tracking_token`; only its hash is persisted. Protect the raw token as a secret; it grants access to the one order.

## Staff status transitions

Guest confirmation: pending -> confirmed. Staff: confirmed -> preparing -> ready. Cancellation is allowed only while pending/confirmed/preparing. Invalid transitions return 409. No API in this service creates robot tasks or controls robots.

## Assistant response shape

```json
{
  "session_id": "opaque-session-id",
  "response": "I have prepared a draft; review it before confirming.",
  "intent": "order",
  "proposed_items": [{"menu_item_id": 2, "name": "Garden salad", "quantity": 1, "unit_price": 13.0}],
  "security_flagged": false
}
```

Gemini outputs are validated against the available catalog; invalid item names and quantities are discarded. The assistant does not place an order until an explicit confirmation API request.

The confirmation body must include `"text": "confirm"` and may include `guest_name` and `room_number`. When supplied, those fields provide the guest details at confirmation time; otherwise the API uses details saved when the conversation began. A name and room are required before an order can be placed.

## AprilTag payload

```json
{
  "room_number": "204",
  "floor_id": "2",
  "observed_family": "tag36h11",
  "observed_tag_id": 73,
  "decision_margin": 55.0
}
```

`verified` is true only when the reporter token is valid and the observed family, ID, room, floor match a staff mapping and the margin is at least 35. Unknown mappings, mismatches, and low-confidence observations return false.
