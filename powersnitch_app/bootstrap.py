from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from powersnitch_app.config import Settings, get_settings
from powersnitch_app.db import Database
from powersnitch_app.storage import Repository


async def ensure_bootstrap(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{settings.sqlite_path}")
    command.upgrade(alembic_cfg, "head")

    db = Database(settings)
    repo = Repository(db)
    await repo.initialize_defaults(settings.initial_password, settings.initial_password_file)


def main() -> None:
    asyncio.run(ensure_bootstrap())


if __name__ == "__main__":
    main()
