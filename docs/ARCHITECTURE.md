# Architecture

## High-level design

The system is split into three layers:

1. Frontend guest services dashboard
2. Backend API and persistence layer
3. Robot integration adapter with a mock simulator

This keeps the hotel guest experience and robotics control decoupled while sharing the same order and delivery state model.

## Backend domain model

- Orders contain guest, room, type, notes, and items
- Order items are persisted with quantity and price
- Delivery tasks are linked one-to-one with orders
- Room verification and robot state are tracked separately from order state
- Audit events record state and operational transitions
- Voice sessions capture a guest conversation transcript for traceability

## Application flow

- Guest creates an order via the website
- Order enters the `pending` state
- Order is `confirmed` by hotel staff or automation
- Order is `ready` once final preparation is complete
- Only then may a delivery task be created and queued
- Robot execution updates delivery status and requires room verification before final completion

## Security and guard rails

- No direct shell execution by LLMs
- No direct SQL execution from guest-facing interfaces
- No direct motor control from website or voice agent
- No delivery task creation before readiness
- No completion without room verification passed

## Robot integration contract

The robot adapter is intentionally isolated behind a simple interface that exposes:

- robot status
- room verification status
- delivery task state transitions
- telemetry recording

The mock backend version simulates the deployment contract locally without requiring a physical robot.
