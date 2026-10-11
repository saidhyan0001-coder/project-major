from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent, DeliveryTask, Order, OrderItem, RobotStatus, VoiceSession


VALID_ORDER_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"ready", "cancelled"},
    "ready": {"assigned", "cancelled"},
    "assigned": {"in_transit", "cancelled"},
    "in_transit": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}


def calculate_order_total(items: list[dict[str, Any]]) -> float:
    return round(sum(item["quantity"] * item["unit_price"] for item in items), 2)


def log_event(db: Session, entity_type: str, entity_id: str, event_type: str, details: str | None = None) -> None:
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=str(entity_id),
        event_type=event_type,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()


def ensure_valid_order_transition(current_status: str, next_status: str) -> None:
    allowed = VALID_ORDER_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise ValueError(f"Invalid order transition from {current_status} to {next_status}")


def set_order_status(db: Session, order: Order, next_status: str) -> Order:
    ensure_valid_order_transition(order.status, next_status)
    order.status = next_status
    order.updated_at = datetime.utcnow()
    db.add(order)
    db.commit()
    db.refresh(order)
    log_event(db, "order", order.id, "status_changed", f"{order.status}")
    return order


def create_order_record(db: Session, payload: dict[str, Any]) -> Order:
    order = Order(
        guest_name=payload["guest_name"],
        room_number=payload["room_number"],
        order_type=payload.get("order_type", "food"),
        notes=payload.get("notes"),
        status="pending",
        total_amount=0.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    item_list = []
    for item in payload["items"]:
        order_item = OrderItem(
            name=item["name"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            order_id=order.id,
        )
        db.add(order_item)
        item_list.append(order_item)

    db.commit()
    order.total_amount = round(sum(i.quantity * i.unit_price for i in item_list), 2)
    db.add(order)
    db.commit()
    db.refresh(order)
    log_event(db, "order", order.id, "created", f"Guest {order.guest_name} purchased {len(item_list)} items")
    return order


def create_delivery_task_for_order(db: Session, order: Order, room_tag_id: str | None = None, robot_name: str = "mock-robot-01") -> DeliveryTask:
    if order.status != "ready":
        raise ValueError("Orders can only be queued for delivery after they are confirmed and marked ready.")

    existing = db.query(DeliveryTask).filter(DeliveryTask.order_id == order.id).first()
    if existing:
        return existing

    task = DeliveryTask(
        order_id=order.id,
        robot_name=robot_name,
        room_tag_id=room_tag_id,
        status="queued",
        room_verification_passed=False,
        estimated_eta_minutes=12,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    log_event(db, "delivery_task", task.id, "queued", f"Delivery queued for room {order.room_number}")
    return task


def update_robot_status(db: Session, state: str, location: str | None, battery_level: int) -> RobotStatus:
    status = db.query(RobotStatus).first()
    if status is None:
        status = RobotStatus(state=state, location=location, battery_level=battery_level)
        db.add(status)
    else:
        status.state = state
        status.location = location
        status.battery_level = battery_level
        status.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(status)
    log_event(db, "robot", status.id, "status_changed", f"state={state} location={location}")
    return status


def create_voice_session(db: Session, guest_name: str | None, channel: str) -> VoiceSession:
    import uuid

    session = VoiceSession(
        session_id=str(uuid.uuid4()),
        guest_name=guest_name,
        channel=channel,
        status="started",
        transcript="",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def append_voice_turn(db: Session, session_id: str, text: str) -> str:
    session = db.query(VoiceSession).filter(VoiceSession.session_id == session_id).first()
    if session is None:
        raise ValueError("Voice session not found")

    if not session.transcript:
        session.transcript = text
    else:
        session.transcript = f"{session.transcript}\n{text}"
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()

    summary = "I can help with room service and delivery updates."
    if "order" in text.lower() or "food" in text.lower():
        summary = "I can help you place a hotel order. Please use the website or the app to confirm the order details."
    if "status" in text.lower() or "delivery" in text.lower():
        summary = "Your delivery status can be checked in the app or through the hotel operation panel."

    return summary
