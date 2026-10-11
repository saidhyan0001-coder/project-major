from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db_session, init_db
from app.models import DeliveryTask, Order, RobotStatus, VoiceSession
from app.schemas import (
    DeliveryTaskCreate,
    DeliveryTaskRead,
    DeliveryTaskUpdate,
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
    RobotStatusRead,
    RobotStatusUpdate,
    VoicePrompt,
    VoicePromptResponse,
    VoiceSessionCreate,
    VoiceSessionRead,
)
from app.services import (
    append_voice_turn,
    calculate_order_total,
    create_delivery_task_for_order,
    create_order_record,
    create_voice_session,
    set_order_status,
    update_robot_status,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        if db.query(RobotStatus).first() is None:
            update_robot_status(db, "idle", "dock", 100)
    finally:
        db.close()
    yield


app = FastAPI(title="Autonomous Hotel Delivery Robot", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hotel-delivery-backend"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "service": "hotel-delivery-backend"}


@app.get("/api/orders", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db_session)) -> list[OrderRead]:
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders


@app.post("/api/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db_session)) -> Order:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must include at least one item")
    order = create_order_record(db, payload.model_dump())
    return order


@app.get("/api/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db_session)) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/api/orders/{order_id}/confirm", response_model=OrderRead)
def confirm_order(order_id: int, db: Session = Depends(get_db_session)) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        order = set_order_status(db, order, "confirmed")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return order


@app.post("/api/orders/{order_id}/prepare", response_model=OrderRead)
def prepare_order(order_id: int, db: Session = Depends(get_db_session)) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        order = set_order_status(db, order, "ready")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return order


@app.post("/api/orders/{order_id}/cancel", response_model=OrderRead)
def cancel_order(order_id: int, db: Session = Depends(get_db_session)) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        order = set_order_status(db, order, "cancelled")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return order


@app.get("/api/delivery-tasks", response_model=list[DeliveryTaskRead])
def list_delivery_tasks(db: Session = Depends(get_db_session)) -> list[DeliveryTask]:
    return db.query(DeliveryTask).order_by(DeliveryTask.created_at.desc()).all()


@app.post("/api/delivery-tasks", response_model=DeliveryTaskRead, status_code=status.HTTP_201_CREATED)
def create_delivery_task(payload: DeliveryTaskCreate, db: Session = Depends(get_db_session)) -> DeliveryTask:
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        task = create_delivery_task_for_order(db, order, payload.room_tag_id, payload.robot_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return task


@app.patch("/api/delivery-tasks/{task_id}", response_model=DeliveryTaskRead)
def update_delivery_task(task_id: int, payload: DeliveryTaskUpdate, db: Session = Depends(get_db_session)) -> DeliveryTask:
    task = db.query(DeliveryTask).filter(DeliveryTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Delivery task not found")

    if payload.robot_name is not None:
        task.robot_name = payload.robot_name
    if payload.room_tag_id is not None:
        task.room_tag_id = payload.room_tag_id
    if payload.room_verification_passed is not None:
        task.room_verification_passed = payload.room_verification_passed
    if payload.status:
        if payload.status == "delivered" and not task.room_verification_passed:
            raise HTTPException(status_code=400, detail="Delivery cannot be marked complete without room verification.")
        task.status = payload.status
    task.updated_at = __import__("datetime").datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/api/robot/status", response_model=RobotStatusRead)
def get_robot_status(db: Session = Depends(get_db_session)) -> RobotStatus:
    status_row = db.query(RobotStatus).first()
    if status_row is None:
        return update_robot_status(db, "idle", "dock", 100)
    return status_row


@app.post("/api/robot/status", response_model=RobotStatusRead)
def set_robot_status(payload: RobotStatusUpdate, db: Session = Depends(get_db_session)) -> RobotStatus:
    return update_robot_status(db, payload.state, payload.location, payload.battery_level)


@app.post("/api/voice/sessions", response_model=VoiceSessionRead, status_code=status.HTTP_201_CREATED)
def create_voice_session_route(payload: VoiceSessionCreate, db: Session = Depends(get_db_session)) -> VoiceSession:
    return create_voice_session(db, payload.guest_name, payload.channel)


@app.post("/api/voice/handle", response_model=VoicePromptResponse)
def handle_voice_prompt(payload: VoicePrompt, db: Session = Depends(get_db_session)) -> VoicePromptResponse:
    try:
        response_text = append_voice_turn(db, payload.session_id, payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VoicePromptResponse(session_id=payload.session_id, response=response_text)


@app.get("/api/health")
def backend_api_health() -> dict[str, str]:
    return {"status": "ok", "service": "hotel-delivery-backend"}
