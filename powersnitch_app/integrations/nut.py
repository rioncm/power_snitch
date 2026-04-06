from __future__ import annotations

import asyncio
import shlex
from datetime import UTC, datetime
from typing import Any

from powersnitch_app.models import DeviceSnapshot


class NutClient:
    def __init__(self, list_command: str, status_command_template: str):
        self.list_command = list_command
        self.status_command_template = status_command_template

    async def discover(self) -> list[str]:
        try:
            process = await asyncio.create_subprocess_exec(
                *shlex.split(self.list_command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return []
        stdout, _stderr = await process.communicate()
        if process.returncode != 0:
            return []
        return [line.strip() for line in stdout.decode().splitlines() if line.strip()]

    async def fetch_status(self, identifier: str) -> dict[str, str]:
        command = self.status_command_template.format(identifier=identifier)
        try:
            process = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("NUT command not found") from exc
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(stderr.decode().strip() or f"failed to fetch {identifier}")
        return parse_upsc(stdout.decode())

    async def snapshot(self, identifier: str) -> DeviceSnapshot:
        data = await self.fetch_status(identifier)
        return snapshot_from_status(identifier, data)


def parse_upsc(raw_output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in raw_output.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().split("#", 1)[0].strip()
    return result


def _float_or_none(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def snapshot_from_status(identifier: str, status: dict[str, str]) -> DeviceSnapshot:
    ups_status = status.get("ups.status", "")
    flags = {flag for flag in ups_status.split() if flag}
    return DeviceSnapshot(
        identifier=identifier,
        observed_at=datetime.now(UTC).replace(microsecond=0),
        status_flags=flags,
        battery_charge=_float_or_none(status.get("battery.charge")),
        runtime_seconds=_float_or_none(status.get("battery.runtime")),
        input_voltage=_float_or_none(status.get("input.voltage")),
        output_voltage=_float_or_none(status.get("output.voltage")),
        load_percent=_float_or_none(status.get("ups.load")),
        raw_data=status,
        is_reachable=bool(status),
    )


def metadata_from_status(status: dict[str, str]) -> dict[str, Any]:
    return {
        "vendor": status.get("device.mfr") or status.get("ups.mfr"),
        "model": status.get("device.model") or status.get("ups.model"),
        "serial": status.get("device.serial") or status.get("ups.serial"),
    }
