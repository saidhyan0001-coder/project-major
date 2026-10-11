# Repository Audit

## Summary

This repository was created as a fresh project structure for the Autonomous Hotel Delivery Robot system because no existing source tree was present in the current working directory. The implementation therefore started from the required architecture rather than modifying an existing application.

## Operating environment

- OS: Windows 11 / PowerShell
- Python: 3.11.9
- Node.js: 24.15.0
- npm: 11.12.1

## Runtime inventory

- Backend: FastAPI 0.115.x, SQLAlchemy 2.0.x, SQLite for local persistence
- Frontend: React 19.x, TypeScript, Vite 8.x
- Test tooling: pytest, Vitest, Testing Library

## Component inventory

- `backend/app/main.py`: FastAPI application and routes
- `backend/app/models.py`: Database schema for orders, delivery tasks, robot status, and voice sessions
- `backend/app/schemas.py`: Request and response validation
- `backend/app/services.py`: Business logic for order state transitions and task creation
- `backend/app/database.py`: Database configuration and SQLAlchemy session management
- `frontend/src/App.tsx`: Guest order, delivery, and robot status dashboard
- `robot_integration/`: Placeholder integration surface for real robotic systems
- `docs/`: Requirement and architecture documentation

## Endpoint inventory

- `GET /health` - Liveness endpoint
- `GET /ready` - Readiness endpoint
- `GET /api/orders` - List orders
- `POST /api/orders` - Create a new order
- `GET /api/orders/{order_id}` - Fetch a single order
- `POST /api/orders/{order_id}/confirm` - Advance order to confirmed
- `POST /api/orders/{order_id}/prepare` - Advance order to ready
- `POST /api/orders/{order_id}/cancel` - Cancel order
- `GET /api/delivery-tasks` - List delivery tasks
- `POST /api/delivery-tasks` - Queue a delivery task only when the order is ready
- `PATCH /api/delivery-tasks/{task_id}` - Update task and room verification state
- `GET /api/robot/status` - Read robot state
- `POST /api/robot/status` - Update robot state
- `POST /api/voice/sessions` - Create a voice session
- `POST /api/voice/handle` - Send voice prompts to the mock voice-ordering service

## Protected / non-changeable components

- ROS 2 workspace and physical robot drivers were not present in this working directory and therefore not modified.
- The project deliberately avoids direct hardware control from the web layer or a general-purpose LLM.
- The order lifecycle enforces a state transition rule and blocks queueing before readiness.

## Risks and remaining gaps

- Real AprilTag detection and ROS 2 integration require the actual robot hardware and ROS workspace not available in this environment.
- Real telephony, speech-to-text, and text-to-speech integrations remain mocked or stubbed for local testing.
- External payments or live hotel systems are intentionally out of scope for local development.
