from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderItemBase(BaseModel):
    name: str
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=0.0, ge=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    id: int
    order_id: int
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    guest_name: str
    room_number: str
    order_type: str = "food"
    notes: Optional[str] = None
    items: List[OrderItemCreate]


class OrderRead(BaseModel):
    id: int
    guest_name: str
    room_number: str
    order_type: str
    status: str
    total_amount: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemRead]
    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str


class DeliveryTaskCreate(BaseModel):
    order_id: int
    robot_name: str = "mock-robot-01"
    room_tag_id: str | None = None
    estimated_eta_minutes: int = 12


class DeliveryTaskUpdate(BaseModel):
    status: str = "queued"
    room_verification_passed: bool | None = None
    room_tag_id: str | None = None
    robot_name: str | None = None


class DeliveryTaskRead(BaseModel):
    id: int
    order_id: int
    robot_name: str
    room_tag_id: str | None = None
    status: str
    room_verification_passed: bool
    estimated_eta_minutes: int | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RobotStatusRead(BaseModel):
    id: int | None = None
    state: str
    location: str | None = None
    battery_level: int
    last_updated: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class RobotStatusUpdate(BaseModel):
    state: str = "idle"
    location: str | None = None
    battery_level: int = 100


class VoiceSessionCreate(BaseModel):
    guest_name: str | None = None
    channel: str = "phone"


class VoiceSessionRead(BaseModel):
    id: int
    session_id: str
    channel: str
    guest_name: str | None = None
    status: str
    transcript: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VoicePrompt(BaseModel):
    session_id: str
    text: str


class VoicePromptResponse(BaseModel):
    session_id: str
    response: str
    order_created: bool = False
    order_id: int | None = None
