from __future__ import annotations

import asyncio

from powersnitch_app.config import get_settings
from powersnitch_app.storage import Database


async def bootstrap() -> None:
    settings = get_settings()
    db = Database(settings.sqlite_path)
    await db.initialize(settings.initial_password, settings.initial_password_file)


def main() -> None:
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()
