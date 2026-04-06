from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from powersnitch_app.db import Database
from powersnitch_app.db_models import (
    ActiveCondition,
    AlertEvent,
    AlertRule,
    AppSetting,
    NotificationChannel,
    NotificationService,
    TelemetrySample,
    UPSDevice,
    User,
)
from powersnitch_app.models import CONDITIONS, DeviceSnapshot
from powersnitch_app.security import hash_password


def utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class Repository:
    def __init__(self, db: Database):
        self.db = db

    async def initialize_defaults(self, initial_password: str | None, password_file: Path) -> str:
        defaults = {
            "bind_mode": "lan",
            "bootstrap_complete": "1",
            "graphs_backend": "sqlite",
        }
        async with self.db.session() as session:
            for key, value in defaults.items():
                existing = await session.get(AppSetting, key)
                if not existing:
                    session.add(AppSetting(key=key, value=value, updated_at=utcnow()))

            admin = await session.scalar(select(User).where(User.username == "admin"))
            generated_password = ""
            if not admin:
                generated_password = initial_password or secrets.token_urlsafe(14)
                session.add(
                    User(
                        username="admin",
                        password_hash=hash_password(generated_password),
                        password_changed=False,
                        created_at=utcnow(),
                        updated_at=utcnow(),
                    )
                )
            await session.commit()

        if generated_password:
            password_file.parent.mkdir(parents=True, exist_ok=True)
            password_file.write_text(generated_password + "\n", encoding="utf-8")
        return generated_password

    async def get_admin(self) -> dict[str, Any] | None:
        async with self.db.session() as session:
            user = await session.scalar(select(User).where(User.username == "admin"))
            return self._user_to_dict(user) if user else None

    async def update_password(self, password_hash: str) -> None:
        async with self.db.session() as session:
            user = await session.scalar(select(User).where(User.username == "admin"))
            if not user:
                return
            user.password_hash = password_hash
            user.password_changed = True
            user.updated_at = utcnow()
            await session.commit()

    async def list_devices(self) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.scalars(select(UPSDevice).order_by(UPSDevice.display_name))
            return [self._device_to_dict(row) for row in rows.all()]

    async def get_device(self, device_id: int) -> dict[str, Any] | None:
        async with self.db.session() as session:
            device = await session.get(UPSDevice, device_id)
            return self._device_to_dict(device) if device else None

    async def upsert_device(self, identifier: str, display_name: str, metadata: dict[str, Any]) -> int:
        async with self.db.session() as session:
            existing = await session.scalar(select(UPSDevice).where(UPSDevice.identifier == identifier))
            now = utcnow()
            if existing:
                existing.display_name = display_name
                existing.vendor = metadata.get("vendor")
                existing.model = metadata.get("model")
                existing.serial = metadata.get("serial")
                existing.updated_at = now
                await session.commit()
                return int(existing.id)
            device = UPSDevice(
                identifier=identifier,
                display_name=display_name,
                vendor=metadata.get("vendor"),
                model=metadata.get("model"),
                serial=metadata.get("serial"),
                created_at=now,
                updated_at=now,
            )
            session.add(device)
            await session.commit()
            await session.refresh(device)
            return int(device.id)

    async def update_device_settings(
        self,
        device_id: int,
        display_name: str,
        enabled: bool,
        poll_interval_seconds: int,
        battery_low_pct_threshold: float,
        runtime_low_threshold_seconds: float,
    ) -> None:
        async with self.db.session() as session:
            device = await session.get(UPSDevice, device_id)
            if not device:
                return
            device.display_name = display_name
            device.enabled = enabled
            device.poll_interval_seconds = poll_interval_seconds
            device.battery_low_pct_threshold = battery_low_pct_threshold
            device.runtime_low_threshold_seconds = runtime_low_threshold_seconds
            device.updated_at = utcnow()
            await session.commit()

    async def save_snapshot(self, device_id: int, snapshot: DeviceSnapshot) -> None:
        async with self.db.session() as session:
            device = await session.get(UPSDevice, device_id)
            if not device:
                return
            device.last_seen_at = snapshot.observed_at
            device.last_snapshot_json = json.dumps(snapshot.raw_data)
            device.updated_at = utcnow()
            session.add(
                TelemetrySample(
                    ups_device_id=device_id,
                    observed_at=snapshot.observed_at,
                    battery_charge=snapshot.battery_charge,
                    runtime_seconds=snapshot.runtime_seconds,
                    input_voltage=snapshot.input_voltage,
                    output_voltage=snapshot.output_voltage,
                    load_percent=snapshot.load_percent,
                    status_flags=",".join(sorted(snapshot.status_flags)),
                    raw_json=json.dumps(snapshot.raw_data),
                )
            )
            await session.commit()

    async def list_services(self) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(NotificationService).order_by(NotificationService.service_type, NotificationService.name)
            )
            return [self._service_to_dict(row) for row in rows.all()]

    async def create_service(self, service_type: str, name: str, config: dict[str, Any]) -> None:
        async with self.db.session() as session:
            service = NotificationService(
                service_type=service_type,
                name=name,
                config_json=json.dumps(config),
                enabled=True,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            session.add(service)
            await session.commit()

    async def list_channels(self) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(NotificationChannel)
                .options(joinedload(NotificationChannel.service))
                .order_by(NotificationChannel.name)
            )
            return [self._channel_to_dict(row) for row in rows.all()]

    async def create_channel(
        self,
        name: str,
        service_id: int,
        target: dict[str, Any],
        extra_text: str,
    ) -> None:
        async with self.db.session() as session:
            channel = NotificationChannel(
                name=name,
                service_id=service_id,
                target_json=json.dumps(target),
                extra_text=extra_text,
                enabled=True,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            session.add(channel)
            await session.commit()

    async def list_rules(self) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(AlertRule)
                .options(joinedload(AlertRule.device), joinedload(AlertRule.channel))
                .order_by(AlertRule.condition_key, AlertRule.id)
            )
            return [self._rule_summary_to_dict(row) for row in rows.all()]

    async def create_rule(
        self,
        ups_device_id: int,
        condition_key: str,
        channel_id: int,
        repeat_interval_seconds: int,
        send_recovery: bool,
    ) -> None:
        if condition_key not in CONDITIONS:
            raise ValueError("Unknown condition key")
        async with self.db.session() as session:
            rule = AlertRule(
                ups_device_id=ups_device_id,
                condition_key=condition_key,
                channel_id=channel_id,
                repeat_interval_seconds=repeat_interval_seconds,
                send_recovery=send_recovery,
                enabled=True,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            session.add(rule)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()

    async def get_rules_for_device(self, device_id: int) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(AlertRule)
                .options(
                    joinedload(AlertRule.channel).joinedload(NotificationChannel.service),
                    joinedload(AlertRule.device),
                )
                .where(AlertRule.ups_device_id == device_id, AlertRule.enabled.is_(True))
            )
            return [self._rule_detail_to_dict(row) for row in rows.all() if row.channel]

    async def get_active_condition(self, device_id: int, condition_key: str) -> dict[str, Any] | None:
        async with self.db.session() as session:
            row = await session.scalar(
                select(ActiveCondition).where(
                    ActiveCondition.ups_device_id == device_id,
                    ActiveCondition.condition_key == condition_key,
                )
            )
            return self._active_condition_to_dict(row) if row else None

    async def open_or_update_active_condition(
        self,
        device_id: int,
        condition_key: str,
        value: Any,
        reason: str,
        mark_alerted: bool = False,
    ) -> None:
        async with self.db.session() as session:
            row = await session.scalar(
                select(ActiveCondition).where(
                    ActiveCondition.ups_device_id == device_id,
                    ActiveCondition.condition_key == condition_key,
                )
            )
            now = utcnow()
            if row:
                row.last_value = json.dumps(value)
                row.last_reason = reason
                if mark_alerted:
                    row.last_alerted_at = now
            else:
                row = ActiveCondition(
                    ups_device_id=device_id,
                    condition_key=condition_key,
                    active_since=now,
                    last_alerted_at=now if mark_alerted else None,
                    last_value=json.dumps(value),
                    last_reason=reason,
                )
                session.add(row)
            await session.commit()

    async def mark_condition_alerted(self, device_id: int, condition_key: str) -> None:
        async with self.db.session() as session:
            row = await session.scalar(
                select(ActiveCondition).where(
                    ActiveCondition.ups_device_id == device_id,
                    ActiveCondition.condition_key == condition_key,
                )
            )
            if row:
                row.last_alerted_at = utcnow()
                await session.commit()

    async def clear_active_condition(self, device_id: int, condition_key: str) -> None:
        async with self.db.session() as session:
            await session.execute(
                delete(ActiveCondition).where(
                    ActiveCondition.ups_device_id == device_id,
                    ActiveCondition.condition_key == condition_key,
                )
            )
            await session.commit()

    async def list_active_conditions(self) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.execute(
                select(ActiveCondition, UPSDevice.display_name)
                .join(UPSDevice, UPSDevice.id == ActiveCondition.ups_device_id)
                .order_by(desc(ActiveCondition.active_since))
            )
            return [
                {
                    **self._active_condition_to_dict(condition),
                    "display_name": display_name,
                }
                for condition, display_name in rows.all()
            ]

    async def log_alert_event(
        self,
        device_id: int | None,
        channel_id: int | None,
        condition_key: str,
        condition_state: str,
        provider: str,
        target: str,
        success: bool,
        payload: dict[str, Any],
        response_code: int | None = None,
        error_message: str | None = None,
    ) -> None:
        async with self.db.session() as session:
            session.add(
                AlertEvent(
                    occurred_at=utcnow(),
                    ups_device_id=device_id,
                    channel_id=channel_id,
                    condition_key=condition_key,
                    condition_state=condition_state,
                    provider=provider,
                    target=target,
                    success=success,
                    response_code=response_code,
                    error_message=error_message,
                    payload_json=json.dumps(payload),
                )
            )
            await session.commit()

    async def list_recent_alerts(self, limit: int = 50) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.execute(
                select(AlertEvent, UPSDevice.display_name, NotificationChannel.name)
                .outerjoin(UPSDevice, UPSDevice.id == AlertEvent.ups_device_id)
                .outerjoin(NotificationChannel, NotificationChannel.id == AlertEvent.channel_id)
                .order_by(desc(AlertEvent.occurred_at))
                .limit(limit)
            )
            result = []
            for event, display_name, channel_name in rows.all():
                item = self._alert_event_to_dict(event)
                item["display_name"] = display_name
                item["channel_name"] = channel_name
                result.append(item)
            return result

    async def recent_samples_for_device(self, device_id: int, limit: int = 96) -> list[dict[str, Any]]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(TelemetrySample)
                .where(TelemetrySample.ups_device_id == device_id)
                .order_by(desc(TelemetrySample.observed_at))
                .limit(limit)
            )
            samples = [self._sample_to_dict(row) for row in rows.all()]
            samples.reverse()
            return samples

    async def dashboard_counts(self) -> dict[str, int]:
        async with self.db.session() as session:
            device_count = await session.scalar(select(func.count()).select_from(UPSDevice))
            enabled_count = await session.scalar(
                select(func.count()).select_from(UPSDevice).where(UPSDevice.enabled.is_(True))
            )
            alert_count = await session.scalar(
                select(func.count()).select_from(AlertEvent).where(AlertEvent.success.is_(False))
            )
            return {
                "devices": int(device_count or 0),
                "enabled_devices": int(enabled_count or 0),
                "failed_alerts": int(alert_count or 0),
            }

    async def get_setting(self, key: str, default: str | None = None) -> str | None:
        async with self.db.session() as session:
            row = await session.get(AppSetting, key)
            return row.value if row else default

    async def set_setting(self, key: str, value: str) -> None:
        async with self.db.session() as session:
            row = await session.get(AppSetting, key)
            if row:
                row.value = value
                row.updated_at = utcnow()
            else:
                session.add(AppSetting(key=key, value=value, updated_at=utcnow()))
            await session.commit()

    def _user_to_dict(self, row: User) -> dict[str, Any]:
        return {
            "id": row.id,
            "username": row.username,
            "password_hash": row.password_hash,
            "password_changed": row.password_changed,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    def _device_to_dict(self, row: UPSDevice) -> dict[str, Any]:
        return {
            "id": row.id,
            "identifier": row.identifier,
            "display_name": row.display_name,
            "enabled": row.enabled,
            "poll_interval_seconds": row.poll_interval_seconds,
            "battery_low_pct_threshold": row.battery_low_pct_threshold,
            "runtime_low_threshold_seconds": row.runtime_low_threshold_seconds,
            "vendor": row.vendor,
            "model": row.model,
            "serial": row.serial,
            "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
            "last_snapshot_json": row.last_snapshot_json,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    def _service_to_dict(self, row: NotificationService) -> dict[str, Any]:
        return {
            "id": row.id,
            "service_type": row.service_type,
            "name": row.name,
            "config": json.loads(row.config_json),
            "enabled": row.enabled,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    def _channel_to_dict(self, row: NotificationChannel) -> dict[str, Any]:
        service = row.service
        return {
            "id": row.id,
            "name": row.name,
            "service_id": row.service_id,
            "service_name": service.name if service else None,
            "service_type": service.service_type if service else None,
            "service_config": json.loads(service.config_json) if service else {},
            "target": json.loads(row.target_json),
            "extra_text": row.extra_text,
            "enabled": row.enabled,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    def _rule_summary_to_dict(self, row: AlertRule) -> dict[str, Any]:
        return {
            "id": row.id,
            "ups_device_id": row.ups_device_id,
            "display_name": row.device.display_name if row.device else None,
            "condition_key": row.condition_key,
            "channel_id": row.channel_id,
            "channel_name": row.channel.name if row.channel else None,
            "repeat_interval_seconds": row.repeat_interval_seconds,
            "send_recovery": row.send_recovery,
            "enabled": row.enabled,
        }

    def _rule_detail_to_dict(self, row: AlertRule) -> dict[str, Any]:
        channel = row.channel
        service = channel.service if channel else None
        return {
            "id": row.id,
            "ups_device_id": row.ups_device_id,
            "condition_key": row.condition_key,
            "channel_id": row.channel_id,
            "channel_name": channel.name if channel else None,
            "target": json.loads(channel.target_json) if channel else {},
            "extra_text": channel.extra_text if channel else "",
            "channel_enabled": channel.enabled if channel else False,
            "service_type": service.service_type if service else None,
            "service_name": service.name if service else None,
            "service_config": json.loads(service.config_json) if service else {},
            "service_enabled": service.enabled if service else False,
            "repeat_interval_seconds": row.repeat_interval_seconds,
            "send_recovery": row.send_recovery,
        }

    def _active_condition_to_dict(self, row: ActiveCondition) -> dict[str, Any]:
        return {
            "id": row.id,
            "ups_device_id": row.ups_device_id,
            "condition_key": row.condition_key,
            "active_since": row.active_since.isoformat(),
            "last_alerted_at": row.last_alerted_at.isoformat() if row.last_alerted_at else None,
            "last_value": row.last_value,
            "last_reason": row.last_reason,
        }

    def _alert_event_to_dict(self, row: AlertEvent) -> dict[str, Any]:
        return {
            "id": row.id,
            "occurred_at": row.occurred_at.isoformat(),
            "ups_device_id": row.ups_device_id,
            "channel_id": row.channel_id,
            "condition_key": row.condition_key,
            "condition_state": row.condition_state,
            "provider": row.provider,
            "target": row.target,
            "success": row.success,
            "response_code": row.response_code,
            "error_message": row.error_message,
            "payload_json": row.payload_json,
        }

    def _sample_to_dict(self, row: TelemetrySample) -> dict[str, Any]:
        return {
            "observed_at": row.observed_at.isoformat(),
            "battery_charge": row.battery_charge,
            "runtime_seconds": row.runtime_seconds,
            "input_voltage": row.input_voltage,
            "output_voltage": row.output_voltage,
            "load_percent": row.load_percent,
        }
