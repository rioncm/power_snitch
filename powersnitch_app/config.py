from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    app_name: str = "Power Snitch"
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("POWERSNITCH_DATA_DIR", "/tmp/powersnitch")))
    bind_host: str = field(default_factory=lambda: os.getenv("POWERSNITCH_BIND_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("POWERSNITCH_PORT", "8000")))
    session_secret: str = field(default_factory=lambda: os.getenv("POWERSNITCH_SESSION_SECRET", secrets.token_urlsafe(32)))
    sqlite_path: Path = field(default_factory=lambda: Path(os.getenv("POWERSNITCH_SQLITE_PATH", "")))
    initial_password_file: Path = field(default_factory=lambda: Path(os.getenv("POWERSNITCH_INITIAL_PASSWORD_FILE", "")))
    initial_password: str | None = field(default_factory=lambda: os.getenv("POWERSNITCH_INITIAL_PASSWORD"))
    nut_list_command: str = field(default_factory=lambda: os.getenv("POWERSNITCH_NUT_LIST_COMMAND", "upsc -l"))
    nut_status_command: str = field(default_factory=lambda: os.getenv("POWERSNITCH_NUT_STATUS_COMMAND", "upsc {identifier}"))
    startup_discovery: bool = field(default_factory=lambda: _bool_env("POWERSNITCH_STARTUP_DISCOVERY", True))
    influx_url: str | None = field(default_factory=lambda: os.getenv("POWERSNITCH_INFLUX_URL"))
    influx_org: str | None = field(default_factory=lambda: os.getenv("POWERSNITCH_INFLUX_ORG"))
    influx_bucket: str | None = field(default_factory=lambda: os.getenv("POWERSNITCH_INFLUX_BUCKET"))
    influx_token: str | None = field(default_factory=lambda: os.getenv("POWERSNITCH_INFLUX_TOKEN"))
    influx_verify_tls: bool = field(default_factory=lambda: _bool_env("POWERSNITCH_INFLUX_VERIFY_TLS", True))

    def __post_init__(self) -> None:
        if not str(self.sqlite_path):
            self.sqlite_path = self.data_dir / "powersnitch.db"
        if not str(self.initial_password_file):
            self.initial_password_file = self.data_dir / "initial_admin_password.txt"

    @property
    def templates_dir(self) -> Path:
        return Path(__file__).parent / "web" / "templates"

    @property
    def static_dir(self) -> Path:
        return Path(__file__).parent / "web" / "static"


def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
