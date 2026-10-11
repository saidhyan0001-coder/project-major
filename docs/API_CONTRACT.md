# API Contract

## Conventions

- All API routes are JSON-based
- Errors return HTTP status codes and a human-readable message
- SQLite is used by default for local development
- The API uses a shared order lifecycle model and common delivery-task contract

## Order endpoints

### POST /api/orders

Request body:

```json
{
  "guest_name": "Jane Guest",
  "room_number": "402",
  "order_type": "food",
  "notes": "No onions",
  "items": [
    {"name": "Salad", "quantity": 1, "unit_price": 14.5}
  ]
}
```

Response:

```json
{
  "id": 1,
  "guest_name": "Jane Guest",
  "room_number": "402",
  "order_type": "food",
  "status": "pending",
  "total_amount": 14.5,
  "notes": "No onions",
  "items": [{"id": 1, "name": "Salad", "quantity": 1, "unit_price": 14.5}]
}
```

### POST /api/orders/{id}/confirm

Moves order from `pending` to `confirmed`.

### POST /api/orders/{id}/prepare

Moves order from `confirmed` to `ready`.

### POST /api/orders/{id}/cancel

Moves order to `cancelled` if allowed.

## Delivery-task endpoints

### POST /api/delivery-tasks

Request body:

```json
{
  "order_id": 1,
  "robot_name": "mock-robot-01",
  "room_tag_id": "tag-402",
  "estimated_eta_minutes": 12
}
```

Requires the order to be in `ready` state. Otherwise, it responds with an error.

### PATCH /api/delivery-tasks/{id}

Request body:

```json
{
  "status": "delivered",
  "room_verification_passed": true
}
```

The API rejects deliveries that do not include successful room verification.

## Robot status

### GET /api/robot/status

```json
{
  "state": "idle",
  "location": "dock",
  "battery_level": 100
}
```

## Voice

### POST /api/voice/sessions

Creates a session used for a phone or voice interaction.

### POST /api/voice/handle

Sends a voice prompt and receives a response summary.
