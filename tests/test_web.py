from pathlib import Path

from fastapi.testclient import TestClient

from powersnitch_app.config import Settings
from powersnitch_app.web.app import create_app


def test_login_and_dashboard(tmp_path):
    data_dir = tmp_path / "data"
    settings = Settings(
        data_dir=data_dir,
        sqlite_path=data_dir / "powersnitch.db",
        initial_password_file=data_dir / "initial_admin_password.txt",
        bind_host="127.0.0.1",
        port=8000,
        session_secret="test-secret",
        startup_discovery=False,
        nut_list_command="true",
        nut_status_command="true",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        login_page = client.get("/login")
        assert login_page.status_code == 200
        password = Path(settings.initial_password_file).read_text(encoding="utf-8").strip()
        response = client.post(
            "/login",
            data={"username": "admin", "password": password},
            follow_redirects=False,
        )
        assert response.status_code == 303
        dashboard = client.get("/dashboard")
        assert dashboard.status_code == 200
        assert "Dashboard" in dashboard.text
