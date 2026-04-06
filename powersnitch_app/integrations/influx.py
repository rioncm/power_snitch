from __future__ import annotations

from typing import Any

import aiohttp

from powersnitch_app.config import Settings
from powersnitch_app.models import DeviceSnapshot


class InfluxTelemetryMirror:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.influx_url
            and self.settings.influx_org
            and self.settings.influx_bucket
            and self.settings.influx_token
        )

    async def write_snapshot(self, device_name: str, snapshot: DeviceSnapshot) -> None:
        if not self.enabled:
            return
        fields: list[str] = []
        mapping: dict[str, float | None] = {
            "battery_charge": snapshot.battery_charge,
            "runtime_seconds": snapshot.runtime_seconds,
            "input_voltage": snapshot.input_voltage,
            "output_voltage": snapshot.output_voltage,
            "load_percent": snapshot.load_percent,
        }
        for key, value in mapping.items():
            if value is not None:
                fields.append(f"{key}={value}")
        if not fields:
            return
        escaped_name = device_name.replace(" ", "\\ ")
        line = f"ups_metrics,device={escaped_name} " + ",".join(fields)
        params = {
            "org": self.settings.influx_org,
            "bucket": self.settings.influx_bucket,
            "precision": "s",
        }
        headers = {"Authorization": f"Token {self.settings.influx_token}"}
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.settings.influx_url.rstrip('/')}/api/v2/write",
                params=params,
                data=line,
                headers=headers,
                ssl=self.settings.influx_verify_tls,
            )

