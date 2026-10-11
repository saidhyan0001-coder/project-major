from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    category = Column(String(80), nullable=False)
    description = Column(Text, nullable=False, default="")
    unit_price = Column(Float, nullable=False)
    available = Column(Boolean, nullable=False, default=True)


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
    tracking_token_hash = Column(String(64), nullable=False, unique=True, index=True, default="")

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(180), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0.0)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)

    order = relationship("Order", back_populates="items")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(String(64), primary_key=True)
    guest_name = Column(String(120), nullable=True)
    room_number = Column(String(50), nullable=True)
    status = Column(String(40), nullable=False, default="active")
    draft_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True)
    category = Column(String(80), nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    session_id = Column(String(64), nullable=True, index=True)
    input_fingerprint = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class RoomTagMapping(Base):
    __tablename__ = "room_tag_mappings"

    id = Column(Integer, primary_key=True)
    room_number = Column(String(50), nullable=False, index=True)
    floor_id = Column(String(50), nullable=False)
    tag_family = Column(String(40), nullable=False)
    tag_id = Column(Integer, nullable=False)
    __table_args__ = (
        UniqueConstraint("room_number", "floor_id", name="uq_room_tag_location"),
        UniqueConstraint("tag_family", "tag_id", name="uq_room_tag_identity"),
    )


class AprilTagEvent(Base):
    __tablename__ = "apriltag_events"

    id = Column(Integer, primary_key=True)
    room_number = Column(String(50), nullable=False)
    floor_id = Column(String(50), nullable=False)
    observed_family = Column(String(40), nullable=False)
    observed_tag_id = Column(Integer, nullable=False)
    decision_margin = Column(Float, nullable=False)
    result = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(String(80), nullable=False)
    event_type = Column(String(80), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
