from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

from powersnitch_app.models import CONDITIONS, DeviceSnapshot
from powersnitch_app.security import hash_password


def utcnow() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        password_changed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ups_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 0,
        poll_interval_seconds INTEGER NOT NULL DEFAULT 15,
        battery_low_pct_threshold REAL DEFAULT 25,
        runtime_low_threshold_seconds REAL DEFAULT 300,
        vendor TEXT,
        model TEXT,
        serial TEXT,
        last_seen_at TEXT,
        last_snapshot_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notification_services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT NOT NULL,
        name TEXT NOT NULL UNIQUE,
        config_json TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notification_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        service_id INTEGER NOT NULL,
        target_json TEXT NOT NULL,
        extra_text TEXT DEFAULT '',
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(service_id) REFERENCES notification_services(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alert_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ups_device_id INTEGER NOT NULL,
        condition_key TEXT NOT NULL,
        channel_id INTEGER NOT NULL,
        repeat_interval_seconds INTEGER DEFAULT 900,
        send_recovery INTEGER NOT NULL DEFAULT 1,
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(ups_device_id, condition_key, channel_id),
        FOREIGN KEY(ups_device_id) REFERENCES ups_devices(id),
        FOREIGN KEY(channel_id) REFERENCES notification_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS active_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ups_device_id INTEGER NOT NULL,
        condition_key TEXT NOT NULL,
        active_since TEXT NOT NULL,
        last_alerted_at TEXT,
        last_value TEXT,
        last_reason TEXT,
        UNIQUE(ups_device_id, condition_key),
        FOREIGN KEY(ups_device_id) REFERENCES ups_devices(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alert_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        occurred_at TEXT NOT NULL,
        ups_device_id INTEGER,
        channel_id INTEGER,
        condition_key TEXT NOT NULL,
        condition_state TEXT NOT NULL,
        provider TEXT NOT NULL,
        target TEXT NOT NULL,
        success INTEGER NOT NULL,
        response_code INTEGER,
        error_message TEXT,
        payload_json TEXT NOT NULL,
        FOREIGN KEY(ups_device_id) REFERENCES ups_devices(id),
        FOREIGN KEY(channel_id) REFERENCES notification_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS telemetry_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ups_device_id INTEGER NOT NULL,
        observed_at TEXT NOT NULL,
        battery_charge REAL,
        runtime_seconds REAL,
        input_voltage REAL,
        output_voltage REAL,
        load_percent REAL,
        status_flags TEXT,
        raw_json TEXT NOT NULL,
        FOREIGN KEY(ups_device_id) REFERENCES ups_devices(id)
    )
    """,
]


class Database:
    def __init__(self, path: Path):
        self.path = path

    async def connect(self) -> aiosqlite.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        return db

    async def initialize(self, initial_password: str | None, password_file: Path) -> str:
        db = await self.connect()
        try:
            for statement in SCHEMA:
                await db.execute(statement)
            await db.commit()
            await self._seed_settings(db)
            generated_password = await self._seed_admin(db, initial_password, password_file)
            return generated_password
        finally:
            await db.close()

    async def _seed_settings(self, db: aiosqlite.Connection) -> None:
        now = utcnow()
        defaults = {
            "bind_mode": "localhost",
            "bootstrap_complete": "1",
            "graphs_backend": "sqlite",
        }
        for key, value in defaults.items():
            await db.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (key, value, now),
            )
        await db.commit()

    async def _seed_admin(
        self,
        db: aiosqlite.Connection,
        initial_password: str | None,
        password_file: Path,
    ) -> str:
        async with db.execute("SELECT id FROM users WHERE username = 'admin'") as cursor:
            row = await cursor.fetchone()
        if row:
            return ""
        password = initial_password or secrets.token_urlsafe(14)
        now = utcnow()
        await db.execute(
            """
            INSERT INTO users (username, password_hash, password_changed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("admin", hash_password(password), 0, now, now),
        )
        await db.commit()
        password_file.parent.mkdir(parents=True, exist_ok=True)
        password_file.write_text(password + "\n", encoding="utf-8")
        return password

    async def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> aiosqlite.Row | None:
        db = await self.connect()
        try:
            async with db.execute(query, params) as cursor:
                return await cursor.fetchone()
        finally:
            await db.close()

    async def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[aiosqlite.Row]:
        db = await self.connect()
        try:
            async with db.execute(query, params) as cursor:
                return await cursor.fetchall()
        finally:
            await db.close()

    async def execute(self, query: str, params: tuple[Any, ...] = ()) -> int:
        db = await self.connect()
        try:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.lastrowid
        finally:
            await db.close()

    async def execute_script(self, statements: list[tuple[str, tuple[Any, ...]]]) -> None:
        db = await self.connect()
        try:
            for query, params in statements:
                await db.execute(query, params)
            await db.commit()
        finally:
            await db.close()


class Repository:
    def __init__(self, db: Database):
        self.db = db

    async def get_admin(self) -> dict[str, Any] | None:
        row = await self.db.fetch_one("SELECT * FROM users WHERE username = 'admin'")
        return dict(row) if row else None

    async def update_password(self, password_hash: str) -> None:
        now = utcnow()
        await self.db.execute(
            """
            UPDATE users SET password_hash = ?, password_changed = 1, updated_at = ?
            WHERE username = 'admin'
            """,
            (password_hash, now),
        )

    async def list_devices(self) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all("SELECT * FROM ups_devices ORDER BY display_name")
        return [dict(row) for row in rows]

    async def get_device(self, device_id: int) -> dict[str, Any] | None:
        row = await self.db.fetch_one("SELECT * FROM ups_devices WHERE id = ?", (device_id,))
        return dict(row) if row else None

    async def upsert_device(self, identifier: str, display_name: str, metadata: dict[str, Any]) -> int:
        now = utcnow()
        existing = await self.db.fetch_one(
            "SELECT id FROM ups_devices WHERE identifier = ?",
            (identifier,),
        )
        if existing:
            await self.db.execute(
                """
                UPDATE ups_devices
                SET display_name = ?, vendor = ?, model = ?, serial = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    display_name,
                    metadata.get("vendor"),
                    metadata.get("model"),
                    metadata.get("serial"),
                    now,
                    existing["id"],
                ),
            )
            return int(existing["id"])
        return await self.db.execute(
            """
            INSERT INTO ups_devices (
                identifier, display_name, vendor, model, serial, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                identifier,
                display_name,
                metadata.get("vendor"),
                metadata.get("model"),
                metadata.get("serial"),
                now,
                now,
            ),
        )

    async def update_device_settings(
        self,
        device_id: int,
        display_name: str,
        enabled: bool,
        poll_interval_seconds: int,
        battery_low_pct_threshold: float,
        runtime_low_threshold_seconds: float,
    ) -> None:
        now = utcnow()
        await self.db.execute(
            """
            UPDATE ups_devices
            SET display_name = ?, enabled = ?, poll_interval_seconds = ?,
                battery_low_pct_threshold = ?, runtime_low_threshold_seconds = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                display_name,
                int(enabled),
                poll_interval_seconds,
                battery_low_pct_threshold,
                runtime_low_threshold_seconds,
                now,
                device_id,
            ),
        )

    async def save_snapshot(self, device_id: int, snapshot: DeviceSnapshot) -> None:
        now = utcnow()
        await self.db.execute_script(
            [
                (
                    """
                    UPDATE ups_devices
                    SET last_seen_at = ?, last_snapshot_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        snapshot.observed_at.isoformat(),
                        json.dumps(snapshot.raw_data),
                        now,
                        device_id,
                    ),
                ),
                (
                    """
                    INSERT INTO telemetry_samples (
                        ups_device_id, observed_at, battery_charge, runtime_seconds,
                        input_voltage, output_voltage, load_percent, status_flags, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id,
                        snapshot.observed_at.isoformat(),
                        snapshot.battery_charge,
                        snapshot.runtime_seconds,
                        snapshot.input_voltage,
                        snapshot.output_voltage,
                        snapshot.load_percent,
                        ",".join(sorted(snapshot.status_flags)),
                        json.dumps(snapshot.raw_data),
                    ),
                ),
            ]
        )

    async def list_services(self) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM notification_services ORDER BY service_type, name"
        )
        return [self._decode_service(dict(row)) for row in rows]

    async def create_service(self, service_type: str, name: str, config: dict[str, Any]) -> None:
        now = utcnow()
        await self.db.execute(
            """
            INSERT INTO notification_services (service_type, name, config_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (service_type, name, json.dumps(config), now, now),
        )

    async def list_channels(self) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            """
            SELECT c.*, s.name AS service_name, s.service_type, s.config_json
            FROM notification_channels c
            JOIN notification_services s ON s.id = c.service_id
            ORDER BY c.name
            """
        )
        decoded = []
        for row in rows:
            item = dict(row)
            item["target"] = json.loads(item.pop("target_json"))
            item["service_config"] = json.loads(item.pop("config_json"))
            decoded.append(item)
        return decoded

    async def create_channel(
        self,
        name: str,
        service_id: int,
        target: dict[str, Any],
        extra_text: str,
    ) -> None:
        now = utcnow()
        await self.db.execute(
            """
            INSERT INTO notification_channels (name, service_id, target_json, extra_text, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, service_id, json.dumps(target), extra_text, now, now),
        )

    async def list_rules(self) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            """
            SELECT r.*, d.display_name, c.name AS channel_name
            FROM alert_rules r
            JOIN ups_devices d ON d.id = r.ups_device_id
            JOIN notification_channels c ON c.id = r.channel_id
            ORDER BY d.display_name, r.condition_key, c.name
            """
        )
        return [dict(row) for row in rows]

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
        now = utcnow()
        await self.db.execute(
            """
            INSERT INTO alert_rules (
                ups_device_id, condition_key, channel_id, repeat_interval_seconds, send_recovery,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ups_device_id,
                condition_key,
                channel_id,
                repeat_interval_seconds,
                int(send_recovery),
                now,
                now,
            ),
        )

    async def get_rules_for_device(self, device_id: int) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            """
            SELECT r.*, c.name AS channel_name, c.target_json, c.extra_text, c.enabled AS channel_enabled,
                   s.service_type, s.name AS service_name, s.config_json, s.enabled AS service_enabled
            FROM alert_rules r
            JOIN notification_channels c ON c.id = r.channel_id
            JOIN notification_services s ON s.id = c.service_id
            WHERE r.ups_device_id = ? AND r.enabled = 1
            """,
            (device_id,),
        )
        decoded = []
        for row in rows:
            item = dict(row)
            item["target"] = json.loads(item.pop("target_json"))
            item["service_config"] = json.loads(item.pop("config_json"))
            decoded.append(item)
        return decoded

    async def get_active_condition(self, device_id: int, condition_key: str) -> dict[str, Any] | None:
        row = await self.db.fetch_one(
            "SELECT * FROM active_conditions WHERE ups_device_id = ? AND condition_key = ?",
            (device_id, condition_key),
        )
        return dict(row) if row else None

    async def open_or_update_active_condition(
        self,
        device_id: int,
        condition_key: str,
        value: Any,
        reason: str,
        mark_alerted: bool = False,
    ) -> None:
        current = await self.get_active_condition(device_id, condition_key)
        now = utcnow()
        if current:
            await self.db.execute(
                """
                UPDATE active_conditions
                SET last_value = ?, last_reason = ?, last_alerted_at = CASE
                    WHEN ? IS NULL THEN last_alerted_at
                    ELSE ?
                END
                WHERE id = ?
                """,
                (
                    json.dumps(value),
                    reason,
                    now if mark_alerted else None,
                    now if mark_alerted else None,
                    current["id"],
                ),
            )
            return
        await self.db.execute(
            """
            INSERT INTO active_conditions (
                ups_device_id, condition_key, active_since, last_alerted_at, last_value, last_reason
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                device_id,
                condition_key,
                now,
                now if mark_alerted else None,
                json.dumps(value),
                reason,
            ),
        )

    async def mark_condition_alerted(self, device_id: int, condition_key: str) -> None:
        await self.db.execute(
            """
            UPDATE active_conditions
            SET last_alerted_at = ?
            WHERE ups_device_id = ? AND condition_key = ?
            """,
            (utcnow(), device_id, condition_key),
        )

    async def clear_active_condition(self, device_id: int, condition_key: str) -> None:
        await self.db.execute(
            "DELETE FROM active_conditions WHERE ups_device_id = ? AND condition_key = ?",
            (device_id, condition_key),
        )

    async def list_active_conditions(self) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            """
            SELECT a.*, d.display_name
            FROM active_conditions a
            JOIN ups_devices d ON d.id = a.ups_device_id
            ORDER BY a.active_since DESC
            """
        )
        return [dict(row) for row in rows]

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
        await self.db.execute(
            """
            INSERT INTO alert_events (
                occurred_at, ups_device_id, channel_id, condition_key, condition_state,
                provider, target, success, response_code, error_message, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utcnow(),
                device_id,
                channel_id,
                condition_key,
                condition_state,
                provider,
                target,
                int(success),
                response_code,
                error_message,
                json.dumps(payload),
            ),
        )

    async def list_recent_alerts(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            """
            SELECT a.*, d.display_name, c.name AS channel_name
            FROM alert_events a
            LEFT JOIN ups_devices d ON d.id = a.ups_device_id
            LEFT JOIN notification_channels c ON c.id = a.channel_id
            ORDER BY a.occurred_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]

    async def recent_samples_for_device(self, device_id: int, limit: int = 96) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            """
            SELECT observed_at, battery_charge, runtime_seconds, input_voltage, output_voltage, load_percent
            FROM telemetry_samples
            WHERE ups_device_id = ?
            ORDER BY observed_at DESC
            LIMIT ?
            """,
            (device_id, limit),
        )
        samples = [dict(row) for row in rows]
        samples.reverse()
        return samples

    async def dashboard_counts(self) -> dict[str, int]:
        device_count = await self.db.fetch_one("SELECT COUNT(*) AS count FROM ups_devices")
        enabled_count = await self.db.fetch_one(
            "SELECT COUNT(*) AS count FROM ups_devices WHERE enabled = 1"
        )
        alert_count = await self.db.fetch_one(
            "SELECT COUNT(*) AS count FROM alert_events WHERE success = 0"
        )
        return {
            "devices": int(device_count["count"]),
            "enabled_devices": int(enabled_count["count"]),
            "failed_alerts": int(alert_count["count"]),
        }

    async def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = await self.db.fetch_one("SELECT value FROM app_settings WHERE key = ?", (key,))
        if not row:
            return default
        return str(row["value"])

    async def set_setting(self, key: str, value: str) -> None:
        await self.db.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, utcnow()),
        )

    def _decode_service(self, row: dict[str, Any]) -> dict[str, Any]:
        row["config"] = json.loads(row.pop("config_json"))
        return row
