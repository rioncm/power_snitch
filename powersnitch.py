import uvicorn

from powersnitch_app.config import get_settings
from powersnitch_app.web.app import create_app


def main() -> None:
    settings = get_settings()
    app = create_app(settings)
    uvicorn.run(app, host=settings.bind_host, port=settings.port)


if __name__ == "__main__":
    main()
