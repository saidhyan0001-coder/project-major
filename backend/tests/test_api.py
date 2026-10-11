import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

os.environ["DATABASE_URL"] = "sqlite:///./test_hotel.db"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_order_lifecycle_and_queue_rules():
    create = client.post(
        "/api/orders",
        json={
            "guest_name": "Alice Guest",
            "room_number": "405",
            "order_type": "food",
            "items": [{"name": "Burger", "quantity": 2, "unit_price": 12.5}],
        },
    )
    assert create.status_code == 201, create.text
    order = create.json()
    assert order["status"] == "pending"

    blocked = client.post("/api/delivery-tasks", json={"order_id": order["id"]})
    assert blocked.status_code == 400

    confirmed = client.post(f"/api/orders/{order['id']}/confirm")
    assert confirmed.status_code == 200
    ready = client.post(f"/api/orders/{order['id']}/prepare")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    queued = client.post(
        "/api/delivery-tasks",
        json={"order_id": order["id"], "robot_name": "mock-robot-01", "room_tag_id": "tag-405"},
    )
    assert queued.status_code == 201, queued.text
    assert queued.json()["status"] == "queued"

    robot_status = client.get("/api/robot/status")
    assert robot_status.status_code == 200
    assert robot_status.json()["state"] in {"idle", "charging", "busy"}


def test_health_endpoints():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
