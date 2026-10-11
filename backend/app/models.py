from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String(120), nullable=False)
    room_number = Column(String(50), nullable=False)
    order_type = Column(String(50), nullable=False, default="food")
    status = Column(String(50), nullable=False, default="pending")
    total_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery_task = relationship("DeliveryTask", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(180), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0.0)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)

    order = relationship("Order", back_populates="items")


class DeliveryTask(Base):
    __tablename__ = "delivery_tasks"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    robot_name = Column(String(120), nullable=False, default="mock-robot-01")
    room_tag_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="queued")
    room_verification_passed = Column(Boolean, nullable=False, default=False)
    estimated_eta_minutes = Column(Integer, nullable=True, default=12)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="delivery_task")
    verification_events = relationship("VerificationEvent", back_populates="delivery_task", cascade="all, delete-orphan")


class RoomTagMap(Base):
    __tablename__ = "room_tag_map"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(50), nullable=False, unique=True)
    tag_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class VerificationEvent(Base):
    __tablename__ = "verification_events"

    id = Column(Integer, primary_key=True, index=True)
    delivery_task_id = Column(Integer, ForeignKey("delivery_tasks.id"), nullable=False)
    room_number = Column(String(50), nullable=False)
    tag_id = Column(String(100), nullable=True)
    result = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    delivery_task = relationship("DeliveryTask", back_populates="verification_events")


class RobotStatus(Base):
    __tablename__ = "robot_status"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(50), nullable=False, default="idle")
    location = Column(String(120), nullable=True)
    battery_level = Column(Integer, nullable=False, default=100)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(120), nullable=False, unique=True)
    channel = Column(String(50), nullable=False, default="phone")
    guest_name = Column(String(120), nullable=True)
    status = Column(String(50), nullable=False, default="started")
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(String(80), nullable=False)
    event_type = Column(String(80), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
