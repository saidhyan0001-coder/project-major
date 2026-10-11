"""Create the current assistant schema and upgrade legacy order tables.

Revision ID: 0001_hotel_assistant
Revises:
"""
from alembic import op
from sqlalchemy import inspect, text

from app.database import Base
from app import models  # noqa: F401

revision = "0001_hotel_assistant"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    inspector = inspect(bind)
    if "orders" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("orders")}
        if "tracking_token_hash" not in columns:
            op.add_column("orders", __import__("sqlalchemy").Column("tracking_token_hash", __import__("sqlalchemy").String(64), nullable=False, server_default=""))
        bind.execute(text("UPDATE orders SET tracking_token_hash = 'legacy-order-' || id WHERE tracking_token_hash = ''"))
        op.create_index(
            "ix_orders_tracking_token_hash",
            "orders",
            ["tracking_token_hash"],
            unique=True,
            if_not_exists=True,
        )
    inspector = inspect(bind)
    if "order_items" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("order_items")}
        if "menu_item_id" not in columns:
            op.add_column("order_items", __import__("sqlalchemy").Column("menu_item_id", __import__("sqlalchemy").Integer(), nullable=True))


def downgrade() -> None:
    raise RuntimeError("Initial deployed database migration is irreversible; restore from a verified backup.")
