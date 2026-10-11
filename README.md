# Autonomous Hotel Delivery Robot

This project delivers a hotel-order and delivery workflow with a FastAPI backend, a React + TypeScript frontend, and a mock robot integration layer that simulates delivery, navigation, room verification, and order tracking.

## Supported versions

- Python: 3.11.x
- Node.js: 20.x or 22.x
- npm: 10.x+
- FastAPI: 0.115.x
- React: 18.x
- Vite: 5.x

## Quick start

1. Create a Python venv and install backend dependencies:
   - `python -m venv .venv`
   - `./.venv/Scripts/Activate.ps1` (PowerShell)
   - `pip install -r backend/requirements.txt`
2. Install frontend dependencies:
   - `npm install --prefix frontend`
3. Copy environment values:
   - `Copy-Item .env.example .env` on Windows or `cp .env.example .env`
4. Start the system:
   - `npm run dev`

## Root commands

- `npm run dev` - Runs backend + frontend together.
- `npm run backend` - Starts the FastAPI server.
- `npm run frontend` - Starts the React development server.
- `npm run test` - Runs Python tests and frontend tests.
- `npm run lint` - Runs backend and frontend lint/type checks.
- `npm run db:migrate` - Creates the SQLite database schema.
- `npm run health` - Calls the backend health endpoint.
- `npm run cleanup` - Removes Python cache, node_modules, build artifacts, and temp logs; does not delete databases or user data.

## Architecture

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + SQLAlchemy + SQLite
- Robot integration: mock simulator with room verification rules
- Voice service: local conversation adapter with deterministic mock responses
- Tests: pytest + Vitest + Testing Library

## Features

- Guest ordering via web form
- State-driven order flow: pending -> confirmed -> ready -> assigned -> delivered
- Delivery tasks created only after an order is ready
- Mock robot status and room verification simulation
- Order and delivery tracking in the website and API
- AI voice session stub for hotel guest conversations

## Notes

The repository intentionally keeps robot hardware integration optional. A mock adapter is provided to support local development and CI. Real ROS 2 or external telephony integrations can be attached by implementing the adapter contracts defined in the docs.
