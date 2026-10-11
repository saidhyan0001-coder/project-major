from __future__ import annotations

import logging
import os
import hmac
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db_session, init_db
from app.models import (
    AprilTagEvent,
    AuditEvent,
    ConversationSession,
    MenuItem,
    Order,
    RoomTagMapping,
    SecurityEvent,
)
from app.schemas import (
    AprilTagObservation,
    ConversationCreate,
    ConversationMessage,
    ConversationOrderConfirm,
    ConversationReply,
    GuestOrderCreate,
    MenuItemRead,
    OrderConfirm,
    OrderCreated,
    OrderRead,
    OrderTrack,
    RoomTagRegistration,
    StaffStatusUpdate,
)
from app.services import (
    create_conversation,
    create_order_from_catalog,
    find_order_by_token,
    generate_assistant_reply,
    initialize_catalog,
    inspect_untrusted_input,
    log_event,
    set_conversation_draft,
    set_order_status,
    validate_proposed_items,
)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("hotel_assistant")
rate_buckets: dict[str, deque[float]] = defaultdict(deque)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        initialize_catalog(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Hotel Guest Ordering Assistant", version="1.0.0", lifespan=lifespan)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def basic_rate_limit(request: Request, call_next: Any):
    if request.url.path.startswith("/api/v1/") and request.method != "OPTIONS":
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = rate_buckets[client_ip]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60")):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait and try again."},
            )
        bucket.append(now)
    return await call_next(request)


def require_staff(authorization: str | None = Header(default=None)) -> None:
    configured = os.getenv("STAFF_API_TOKEN")
    if not configured:
        raise HTTPException(status_code=503, detail="Staff access is not configured on this server.")
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {configured}"):
        raise HTTPException(status_code=401, detail="Staff authentication required.")


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hotel-ordering-api"}


@app.get("/ready")
@app.get("/api/v1/ready")
def readiness(db: Session = Depends(get_db_session)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("readiness_database_check_failed")
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready", "database": "ready"}


@app.get("/api/v1/menu", response_model=list[MenuItemRead])
def get_menu(db: Session = Depends(get_db_session)) -> list[MenuItem]:
    return db.query(MenuItem).filter(MenuItem.available.is_(True)).order_by(MenuItem.category, MenuItem.name).all()


@app.post("/api/v1/orders/preview")
def preview_order(payload: GuestOrderCreate, db: Session = Depends(get_db_session)) -> dict[str, Any]:
    ids = [item.menu_item_id for item in payload.items]
    catalog = {item.id: item for item in db.query(MenuItem).filter(MenuItem.id.in_(ids)).all()}
    if len(catalog) != len(set(ids)):
        raise HTTPException(status_code=400, detail="A selected menu item does not exist.")
    lines = []
    for request_item in payload.items:
        menu_item = catalog[request_item.menu_item_id]
        if not menu_item.available:
            raise HTTPException(status_code=400, detail=f"{menu_item.name} is unavailable.")
        lines.append({
            "menu_item_id": menu_item.id,
            "name": menu_item.name,
            "quantity": request_item.quantity,
            "unit_price": menu_item.unit_price,
            "line_total": round(menu_item.unit_price * request_item.quantity, 2),
        })
    return {"items": lines, "total_amount": round(sum(item["line_total"] for item in lines), 2)}


@app.post("/api/v1/orders", response_model=OrderCreated, status_code=status.HTTP_201_CREATED)
def create_guest_order(payload: GuestOrderCreate, db: Session = Depends(get_db_session)) -> OrderCreated:
    try:
        order, token = create_order_from_catalog(
            db,
            payload.guest_name,
            payload.room_number,
            [item.model_dump() for item in payload.items],
            payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrderCreated(**OrderRead.model_validate(order).model_dump(), tracking_token=token)


@app.post("/api/v1/orders/{order_id}/confirm", response_model=OrderRead)
def confirm_guest_order(order_id: int, payload: OrderConfirm, db: Session = Depends(get_db_session)) -> Order:
    order = find_order_by_token(db, payload.tracking_token)
    if order is None or order.id != order_id:
        raise HTTPException(status_code=404, detail="Order not found.")
    try:
        return set_order_status(db, order, "confirmed")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/orders/{order_id}/track", response_model=OrderRead)
def track_guest_order(order_id: int, payload: OrderTrack, db: Session = Depends(get_db_session)) -> Order:
    order = find_order_by_token(db, payload.tracking_token)
    if order is None or order.id != order_id:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


@app.post("/api/v1/orders/{order_id}/cancel", response_model=OrderRead)
def cancel_guest_order(order_id: int, payload: OrderConfirm, db: Session = Depends(get_db_session)) -> Order:
    order = find_order_by_token(db, payload.tracking_token)
    if order is None or order.id != order_id:
        raise HTTPException(status_code=404, detail="Order not found.")
    try:
        return set_order_status(db, order, "cancelled")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/conversations", response_model=dict[str, str])
def start_conversation(payload: ConversationCreate, db: Session = Depends(get_db_session)) -> dict[str, str]:
    session = create_conversation(db, payload.guest_name, payload.room_number)
    return {"session_id": session.id, "status": session.status}


@app.post("/api/v1/conversations/{session_id}/messages", response_model=ConversationReply)
def conversation_message(
    session_id: str,
    payload: ConversationMessage,
    db: Session = Depends(get_db_session),
) -> ConversationReply:
    session = db.query(ConversationSession).filter(ConversationSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    category = inspect_untrusted_input(db, payload.text, session_id)
    if category:
        return ConversationReply(
            session_id=session_id,
            response="I can’t help bypass safeguards, access private information, or change prices. I can still help with the available menu.",
            intent="blocked",
            security_flagged=True,
        )
    menu = db.query(MenuItem).filter(MenuItem.available.is_(True)).all()
    try:
        result = generate_assistant_reply(payload.text, menu, session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    items = validate_proposed_items(result.items or [], menu)
    if result.intent == "order" and not items:
        result.response = "I couldn't match that request to available menu items. Please choose from the menu shown on the website."
        result.intent = "general"
    set_conversation_draft(db, session, items)
    return ConversationReply(
        session_id=session_id,
        response=result.response,
        intent=result.intent,
        proposed_items=items,
    )


@app.post("/api/v1/conversations/{session_id}/confirm", response_model=OrderCreated, status_code=201)
def confirm_conversation_order(
    session_id: str,
    payload: ConversationOrderConfirm,
    db: Session = Depends(get_db_session),
) -> OrderCreated:
    session = db.query(ConversationSession).filter(ConversationSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="This conversation has already placed an order.")
    if payload.text.strip().casefold() != "confirm":
        raise HTTPException(status_code=400, detail="Explicit confirmation text 'confirm' is required.")
    guest_name = (payload.guest_name or session.guest_name or "").strip()
    room_number = (payload.room_number or session.room_number or "").strip()
    if not guest_name or not room_number:
        raise HTTPException(status_code=400, detail="Provide guest name and room number before confirming.")
    import json
    draft = json.loads(session.draft_json)
    try:
        order, token = create_order_from_catalog(
            db,
            guest_name,
            room_number,
            [{"menu_item_id": item["menu_item_id"], "quantity": item["quantity"]} for item in draft],
            confirmation_status="confirmed",
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"Conversation draft is no longer valid: {exc}") from exc
    session.status = "order_placed"
    session.guest_name = guest_name
    session.room_number = room_number
    db.add(session)
    db.commit()
    return OrderCreated(**OrderRead.model_validate(order).model_dump(), tracking_token=token)


@app.get("/api/v1/staff/orders", response_model=list[OrderRead], dependencies=[Depends(require_staff)])
def staff_list_orders(db: Session = Depends(get_db_session)) -> list[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).limit(200).all()


@app.patch("/api/v1/staff/orders/{order_id}/status", response_model=OrderRead, dependencies=[Depends(require_staff)])
def staff_update_order_status(
    order_id: int,
    payload: StaffStatusUpdate,
    db: Session = Depends(get_db_session),
) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    if payload.status not in {"preparing", "ready", "cancelled"}:
        raise HTTPException(status_code=400, detail="Staff may set status to preparing, ready, or cancelled.")
    try:
        updated = set_order_status(db, order, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return updated


@app.get("/api/v1/staff/security-events", dependencies=[Depends(require_staff)])
def staff_security_events(db: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return [
        {
            "id": event.id,
            "category": event.category,
            "severity": event.severity,
            "session_id": event.session_id,
            "created_at": event.created_at,
        }
        for event in db.query(SecurityEvent).order_by(SecurityEvent.created_at.desc()).limit(200).all()
    ]


@app.get("/api/v1/staff/audit-events", dependencies=[Depends(require_staff)])
def staff_audit_events(db: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return [
        {
            "id": event.id,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "event_type": event.event_type,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200).all()
    ]


@app.put("/api/v1/staff/apriltag-mappings", dependencies=[Depends(require_staff)])
def register_apriltag_mapping(
    payload: RoomTagRegistration,
    db: Session = Depends(get_db_session),
) -> dict[str, str | int]:
    mapping = (
        db.query(RoomTagMapping)
        .filter(
            RoomTagMapping.room_number == payload.room_number,
            RoomTagMapping.floor_id == payload.floor_id,
        )
        .first()
    )
    if mapping is None:
        tag_in_use = db.query(RoomTagMapping).filter(
            RoomTagMapping.tag_family == payload.tag_family,
            RoomTagMapping.tag_id == payload.tag_id,
        ).first()
        if tag_in_use:
            raise HTTPException(status_code=409, detail="This tag is already assigned to another room.")
        mapping = RoomTagMapping(**payload.model_dump())
    else:
        tag_in_use = db.query(RoomTagMapping).filter(
            RoomTagMapping.tag_family == payload.tag_family,
            RoomTagMapping.tag_id == payload.tag_id,
            RoomTagMapping.id != mapping.id,
        ).first()
        if tag_in_use:
            raise HTTPException(status_code=409, detail="This tag is already assigned to another room.")
        mapping.tag_family = payload.tag_family
        mapping.tag_id = payload.tag_id
    db.add(mapping)
    db.commit()
    return {"room_number": mapping.room_number, "floor_id": mapping.floor_id, "tag_family": mapping.tag_family, "tag_id": mapping.tag_id}


@app.post("/api/v1/apriltag/observations")
def report_apriltag_observation(
    payload: AprilTagObservation,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    report_token = os.getenv("APRILTAG_REPORT_TOKEN")
    if not report_token:
        raise HTTPException(status_code=503, detail="AprilTag reporting is not configured.")
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {report_token}"):
        raise HTTPException(status_code=401, detail="AprilTag reporter authentication required.")
    mapping = (
        db.query(RoomTagMapping)
        .filter(
            RoomTagMapping.room_number == payload.room_number,
            RoomTagMapping.floor_id == payload.floor_id,
        )
        .first()
    )
    result = "verified" if (
        mapping
        and mapping.tag_family == payload.observed_family
        and mapping.tag_id == payload.observed_tag_id
        and payload.decision_margin >= 35.0
    ) else (
        "unknown_mapping" if mapping is None
        else "low_confidence" if payload.decision_margin < 35.0
        else "mismatch"
    )
    db.add(AprilTagEvent(
        room_number=payload.room_number,
        floor_id=payload.floor_id,
        observed_family=payload.observed_family,
        observed_tag_id=payload.observed_tag_id,
        decision_margin=payload.decision_margin,
        result=result,
    ))
    db.commit()
    return {"verified": result == "verified", "result": result}


@app.get("/api/v1/staff/apriltag-events", dependencies=[Depends(require_staff)])
def staff_apriltag_events(db: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return [
        {
            "id": event.id,
            "room_number": event.room_number,
            "floor_id": event.floor_id,
            "observed_family": event.observed_family,
            "observed_tag_id": event.observed_tag_id,
            "decision_margin": event.decision_margin,
            "result": event.result,
            "created_at": event.created_at,
        }
        for event in db.query(AprilTagEvent).order_by(AprilTagEvent.created_at.desc()).limit(200).all()
    ]
