from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MenuItemRead(BaseModel):
    id: int
    name: str
    category: str
    description: str
    unit_price: float
    available: bool
    model_config = ConfigDict(from_attributes=True)


class GuestOrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1, le=20)


class GuestOrderCreate(BaseModel):
    guest_name: str = Field(min_length=1, max_length=120)
    room_number: str = Field(min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)
    items: list[GuestOrderItemCreate] = Field(min_length=1, max_length=30)


class OrderItemRead(BaseModel):
    id: int
    menu_item_id: int | None
    name: str
    quantity: int
    unit_price: float
    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    guest_name: str
    room_number: str
    order_type: str
    status: str
    total_amount: float
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]
    model_config = ConfigDict(from_attributes=True)


class OrderCreated(OrderRead):
    tracking_token: str


class OrderConfirm(BaseModel):
    tracking_token: str = Field(min_length=20, max_length=100)


class OrderTrack(BaseModel):
    tracking_token: str = Field(min_length=20, max_length=100)


class ConversationCreate(BaseModel):
    guest_name: str | None = Field(default=None, max_length=120)
    room_number: str | None = Field(default=None, max_length=50)


class ConversationMessage(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ConversationOrderConfirm(BaseModel):
    text: str = Field(min_length=1, max_length=20)
    guest_name: str | None = Field(default=None, max_length=120)
    room_number: str | None = Field(default=None, max_length=50)


class ProposedItem(BaseModel):
    menu_item_id: int
    name: str
    quantity: int = Field(ge=1, le=20)
    unit_price: float


class ConversationReply(BaseModel):
    session_id: str
    response: str
    intent: str
    proposed_items: list[ProposedItem] = Field(default_factory=list)
    security_flagged: bool = False


class StaffStatusUpdate(BaseModel):
    status: str


class RoomTagRegistration(BaseModel):
    room_number: str = Field(min_length=1, max_length=50)
    floor_id: str = Field(min_length=1, max_length=50)
    tag_family: str = Field(min_length=1, max_length=40)
    tag_id: int = Field(ge=0, le=65535)


class AprilTagObservation(BaseModel):
    room_number: str = Field(min_length=1, max_length=50)
    floor_id: str = Field(min_length=1, max_length=50)
    observed_family: str = Field(min_length=1, max_length=40)
    observed_tag_id: int = Field(ge=0, le=65535)
    decision_margin: float = Field(ge=0)
