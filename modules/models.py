import aiosqlite
from datetime import datetime
from typing import Any, Dict, Optional

DB_PATH = "/opt/powersnitch/logs.db"

EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    voltage REAL,
    battery_charge REAL,
    runtime_estimate REAL,
    ups_status TEXT,
    raw_json TEXT
);
"""

ALERT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS alert_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    method TEXT NOT NULL,
    target TEXT NOT NULL,
    event_type TEXT NOT NULL,
    success BOOLEAN,
    response_code INTEGER,
    error_message TEXT
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(EVENTS_TABLE)
        await db.execute(ALERT_LOG_TABLE)
        await db.commit()

async def log_poll_event(status: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO events (timestamp, event_type, voltage, battery_charge, runtime_estimate, ups_status, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                status["timestamp"],
                status["event_type"],
                status.get("voltage"),
                status.get("battery_charge"),
                status.get("runtime_estimate"),
                status.get("ups_status"),
                status.get("raw_json")
            )
        )
        await db.commit()

async def log_alert_event(method: str, target: str, event_type: str, success: bool, response_code: Optional[int] = None, error_message: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO alert_log (timestamp, method, target, event_type, success, response_code, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                method,
                target,
                event_type,
                success,
                response_code,
                error_message
            )
        )
        await db.commit()
