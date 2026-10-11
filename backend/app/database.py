import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hotel.db")
if DATABASE_URL.startswith("sqlite:///"):
    database_path = DATABASE_URL.removeprefix("sqlite:///")
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    from app.models import Base as ModelBase

    ModelBase.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "orders" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("orders")}
        with engine.begin() as connection:
            if "tracking_token_hash" not in columns:
                connection.execute(text("ALTER TABLE orders ADD COLUMN tracking_token_hash VARCHAR(64) NOT NULL DEFAULT ''"))
            connection.execute(text("UPDATE orders SET tracking_token_hash = 'legacy-order-' || id WHERE tracking_token_hash = ''"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_tracking_token_hash ON orders (tracking_token_hash)"))
    inspector = inspect(engine)
    if "order_items" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("order_items")}
        if "menu_item_id" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE order_items ADD COLUMN menu_item_id INTEGER REFERENCES menu_items(id)"))


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
