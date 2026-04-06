from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


CONDITIONS: tuple[str, ...] = (
    "on_battery",
    "on_line",
    "low_battery",
    "replace_battery",
    "overload",
    "shutdown_imminent",
    "battery_low_pct",
    "runtime_low",
    "ups_communication_lost",
    "unknown_state",
)

STATUS_FLAGS: dict[str, str] = {
    "on_battery": "OB",
    "on_line": "OL",
    "low_battery": "LB",
    "replace_battery": "RB",
    "overload": "OVER",
    "shutdown_imminent": "FSD",
}


@dataclass(slots=True)
class DeviceSnapshot:
    identifier: str
    observed_at: datetime
    status_flags: set[str]
    battery_charge: float | None
    runtime_seconds: float | None
    input_voltage: float | None
    output_voltage: float | None
    load_percent: float | None
    raw_data: dict[str, Any]
    is_reachable: bool = True


@dataclass(slots=True)
class ConditionResult:
    key: str
    active: bool
    value: float | str | None
    reason: str


@dataclass(slots=True)
class DeliveryResult:
    provider: str
    target: str
    success: bool
    response_code: int | None = None
    error_message: str | None = None

