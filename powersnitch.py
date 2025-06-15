import asyncio
import sys
import uvicorn
from fastapi import FastAPI
from modules.config import load_config_from_yaml
from modules.models import init_db
from modules.monitor import Monitor
from modules.api import app as api_app

CONFIG_PATH = "/opt/powersnitch/config.yaml"

async def main():
    try:
        # Load configuration
        config = load_config_from_yaml(CONFIG_PATH)

        # Initialize database schema
        await init_db()

        # Start monitor loop
        monitor = Monitor(config)
        loop = asyncio.get_event_loop()
        loop.create_task(monitor.monitor_loop())

        # Launch FastAPI API
        api = FastAPI()
        api.mount("/", api_app)

        config_host = "0.0.0.0"
        config_port = 8000
        uvicorn_config = uvicorn.Config(api, host=config_host, port=config_port, log_level="info")
        server = uvicorn.Server(uvicorn_config)
        await server.serve()

    except Exception as e:
        print(f"Startup failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
