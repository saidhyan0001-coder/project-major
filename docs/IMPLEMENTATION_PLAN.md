# Implementation Plan

## Phase 1: repo and runtime setup

- Validate Python and Node runtimes
- Create project structure
- Add environment templates and setup scripts
- Document the architecture and API contract

## Phase 2: backend foundation

- Add FastAPI app, SQLAlchemy models, and session setup
- Implement order lifecycle rules and business validation
- Add delivery-task creation rules and room verification guard rails
- Add health, readiness, robot status, and voice routes

## Phase 3: frontend experience

- Build a Vite React TypeScript dashboard
- Add order form and order action controls
- Display robot status, order queue, and delivery tasks
- Add client-side error handling and status messaging

## Phase 4: test automation and verification

- Validate backend API flow with pytest
- Validate frontend rendering with Vitest and Testing Library
- Run the application locally and check health endpoints
- Confirm the order-to-delivery workflow and constrained task creation rules

## Phase 5: deployment and extension

- Add Docker Compose support for local startup
- Document real robot and telephony integration contracts
- Replace mock adapters with validated external integrations when hardware or credentials become available

## Protected constraints

- No direct robot motor control from website or LLM
- No fake success responses in production mode
- No delivery completion without verified room confirmation
- No hardcoded room coordinates or direct map assumptions
