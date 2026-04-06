from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime, timedelta
from typing import Any

from powersnitch_app.core.conditions import build_alert_text, evaluate_conditions
from powersnitch_app.integrations.influx import InfluxTelemetryMirror
from powersnitch_app.integrations.notifications import NotificationDispatcher
from powersnitch_app.integrations.nut import NutClient, metadata_from_status
from powersnitch_app.models import DeviceSnapshot
from powersnitch_app.storage import Repository


class MonitorService:
    def __init__(
        self,
        repository: Repository,
        nut_client: NutClient,
        notifier: NotificationDispatcher,
        telemetry: InfluxTelemetryMirror,
    ):
        self.repository = repository
        self.nut_client = nut_client
        self.notifier = notifier
        self.telemetry = telemetry
        self._task: asyncio.Task[Any] | None = None
        self._stop = asyncio.Event()

    async def startup(self, discover: bool = True) -> None:
        if discover:
            await self.discover_devices()
        self._stop.clear()
        self._task = asyncio.create_task(self._run())

    async def shutdown(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def discover_devices(self) -> list[dict[str, Any]]:
        discovered: list[dict[str, Any]] = []
        for identifier in await self.nut_client.discover():
            try:
                status = await self.nut_client.fetch_status(identifier)
            except Exception:
                status = {}
            metadata = metadata_from_status(status)
            name = metadata.get("model") or identifier
            device_id = await self.repository.upsert_device(identifier, name.strip(), metadata)
            device = await self.repository.get_device(device_id)
            if device:
                discovered.append(device)
        return discovered

    async def run_once(self) -> None:
        for device in await self.repository.list_devices():
            if not device["enabled"]:
                continue
            await self._poll_device(device)

    async def _run(self) -> None:
        while not self._stop.is_set():
            await self.run_once()
            await asyncio.sleep(10)

    async def _poll_device(self, device: dict[str, Any]) -> None:
        try:
            snapshot = await self.nut_client.snapshot(device["identifier"])
            await self.repository.save_snapshot(device["id"], snapshot)
            await self.telemetry.write_snapshot(device["display_name"], snapshot)
        except Exception:
            snapshot = DeviceSnapshot(
                identifier=device["identifier"],
                observed_at=datetime.now(UTC).replace(microsecond=0),
                status_flags=set(),
                battery_charge=None,
                runtime_seconds=None,
                input_voltage=None,
                output_voltage=None,
                load_percent=None,
                raw_data={},
                is_reachable=False,
            )
        await self._evaluate_device_rules(device, snapshot)

    async def _evaluate_device_rules(self, device: dict[str, Any], snapshot: DeviceSnapshot) -> None:
        results = {
            result.key: result
            for result in evaluate_conditions(
                snapshot,
                float(device["battery_low_pct_threshold"]),
                float(device["runtime_low_threshold_seconds"]),
            )
        }
        rules = await self.repository.get_rules_for_device(int(device["id"]))
        for rule in rules:
            result = results.get(rule["condition_key"])
            if not result:
                continue
            active = await self.repository.get_active_condition(device["id"], rule["condition_key"])
            should_send_active = False
            should_send_recovery = False
            if result.active and not active:
                await self.repository.open_or_update_active_condition(
                    device["id"],
                    result.key,
                    result.value,
                    result.reason,
                )
                should_send_active = True
            elif result.active and active:
                await self.repository.open_or_update_active_condition(
                    device["id"],
                    result.key,
                    result.value,
                    result.reason,
                )
                last_alerted = active["last_alerted_at"]
                if self._interval_due(last_alerted, int(rule["repeat_interval_seconds"] or 0)):
                    should_send_active = True
            elif not result.active and active:
                should_send_recovery = bool(rule["send_recovery"])

            if should_send_active:
                await self._send_rule_alert(device, rule, snapshot, "active")
                await self.repository.mark_condition_alerted(device["id"], result.key)
            elif should_send_recovery:
                await self._send_rule_alert(device, rule, snapshot, "recovered")
                await self.repository.clear_active_condition(device["id"], result.key)
            elif not result.active and active and not should_send_recovery:
                await self.repository.clear_active_condition(device["id"], result.key)

    def _interval_due(self, last_alerted_at: str | None, seconds: int) -> bool:
        if not seconds:
            return False
        if not last_alerted_at:
            return True
        last_time = datetime.fromisoformat(last_alerted_at)
        return datetime.now(UTC) >= last_time + timedelta(seconds=seconds)

    async def _send_rule_alert(
        self,
        device: dict[str, Any],
        rule: dict[str, Any],
        snapshot: DeviceSnapshot,
        state: str,
    ) -> None:
        subject, body = build_alert_text(
            device["display_name"],
            rule["condition_key"],
            state,
            snapshot,
            rule.get("extra_text", ""),
        )
        result = await self.notifier.deliver(
            rule["service_type"],
            rule["service_config"],
            rule["target"],
            subject,
            body,
        )
        payload = {
            "subject": subject,
            "body": body,
            "service_type": rule["service_type"],
            "service_name": rule["service_name"],
            "channel_name": rule["channel_name"],
        }
        await self.repository.log_alert_event(
            device["id"],
            rule["channel_id"],
            rule["condition_key"],
            state,
            result.provider,
            result.target,
            result.success,
            payload,
            result.response_code,
            result.error_message,
        )
