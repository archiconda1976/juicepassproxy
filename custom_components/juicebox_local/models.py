"""Data models for the JuiceBox Local integration."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class JuiceBoxState:
    """Accumulated state received from one JuiceBox."""

    serial: str | None = None
    protocol_version: str | None = None
    status: str | None = None
    current: float | None = None
    current_rating: int | None = None
    current_max_offline: int | None = None
    current_max_online: int | None = None
    frequency: float | None = None
    energy_lifetime: int | None = None
    energy_session: int | None = None
    temperature: float | None = None
    voltage: float | None = None
    power: float | None = None
    power_factor: float | None = None
    debug_message: str | None = None
    desired_offline_current: int | None = None
    desired_online_current: int | None = None
    last_seen: datetime | None = None

    def update_from_message(self, values: dict[str, Any]) -> None:
        """Merge a decoded JuiceBox message into the accumulated state."""
        for key in (
            "serial",
            "protocol_version",
            "status",
            "current",
            "current_rating",
            "current_max_offline",
            "current_max_online",
            "frequency",
            "energy_lifetime",
            "energy_session",
            "temperature",
            "voltage",
            "power",
            "power_factor",
            "debug_message",
        ):
            if key in values and values[key] is not None:
                setattr(self, key, values[key])
