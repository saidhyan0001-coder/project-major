from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RobotStatusSnapshot:
    state: str = "idle"
    location: str = "dock"
    battery_level: int = 100


class MockRobotAdapter:
    """A local simulator used when ROS 2 hardware is unavailable."""

    def __init__(self) -> None:
        self.status = RobotStatusSnapshot()

    def update_status(self, state: str, location: str, battery_level: int) -> RobotStatusSnapshot:
        self.status = RobotStatusSnapshot(state=state, location=location, battery_level=battery_level)
        return self.status

    def verify_room(self, room_number: str, tag_id: str | None) -> bool:
        if not tag_id:
            return False
        return tag_id == f"tag-{room_number}"
