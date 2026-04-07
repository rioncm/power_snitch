from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from powersnitch_app.config import Settings
from powersnitch_app.bootstrap import ensure_bootstrap
from powersnitch_app.core.monitor import MonitorService
from powersnitch_app.db import Database
from powersnitch_app.integrations.influx import InfluxTelemetryMirror
from powersnitch_app.integrations.notifications import NotificationDispatcher
from powersnitch_app.integrations.nut import NutClient
from powersnitch_app.security import hash_password, require_admin, verify_password
from powersnitch_app.storage import Repository


def service_type_fields(service_type: str) -> list[tuple[str, str]]:
    if service_type == "email":
        return [
            ("host", "SMTP Host"),
            ("port", "SMTP Port"),
            ("username", "SMTP Username"),
            ("password", "SMTP Password"),
            ("from_email", "From Email"),
            ("start_tls", "Start TLS (true/false)"),
        ]
    if service_type == "telegram":
        return [("bot_token", "Bot Token")]
    if service_type == "twilio":
        return [
            ("account_sid", "Account SID"),
            ("auth_token", "Auth Token"),
            ("from_number", "From Number"),
        ]
    return [("url", "Default URL"), ("headers_json", "Headers JSON")]


def channel_target_fields(service_type: str) -> list[tuple[str, str]]:
    if service_type == "email":
        return [("to", "Recipients (comma separated)")]
    if service_type == "telegram":
        return [("chat_id", "Chat ID")]
    if service_type == "twilio":
        return [("to_number", "To Number")]
    return [("url", "Webhook URL")]


def parse_service_config(service_type: str, form: dict[str, Any]) -> dict[str, Any]:
    config = {key: value for key, value in form.items() if key not in {"service_type", "name"} and value}
    if service_type == "email":
        config["start_tls"] = str(config.get("start_tls", "true")).lower() in {"1", "true", "yes", "on"}
        config["port"] = int(config.get("port", 587))
    if service_type == "webhook" and config.get("headers_json"):
        config["headers"] = json.loads(config["headers_json"])
        config.pop("headers_json", None)
    return config


def parse_channel_target(service_type: str, form: dict[str, Any]) -> dict[str, Any]:
    target = {key: value for key, value in form.items() if key not in {"name", "service_id", "extra_text"} and value}
    return target


def build_graph_points(samples: list[dict[str, Any]], field: str) -> str:
    values = [sample[field] for sample in samples if sample[field] is not None]
    if len(values) < 2:
        return ""
    maximum = max(values) or 1
    points: list[str] = []
    for index, sample in enumerate(samples):
        value = sample[field]
        if value is None:
            continue
        x = (index / max(len(samples) - 1, 1)) * 280
        y = 80 - (float(value) / maximum) * 70
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def create_app(settings: Settings) -> FastAPI:
    db = Database(settings)
    repository = Repository(db)
    nut_client = NutClient(settings.nut_list_command, settings.nut_status_command)
    monitor = MonitorService(
        repository=repository,
        nut_client=nut_client,
        notifier=NotificationDispatcher(),
        telemetry=InfluxTelemetryMirror(settings),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await ensure_bootstrap(settings)
        await monitor.startup(discover=settings.startup_discovery)
        try:
            yield
        finally:
            await monitor.shutdown()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    templates = Jinja2Templates(directory=str(settings.templates_dir))
    app.state.repository = repository
    app.state.monitor = monitor
    app.state.settings = settings
    app.state.templates = templates

    def redirect(path: str) -> RedirectResponse:
        return RedirectResponse(path, status_code=303)

    async def context(request: Request, **extra: Any) -> dict[str, Any]:
        repo: Repository = request.app.state.repository
        return {
            "request": request,
            "user": request.session.get("username"),
            "bind_mode": await repo.get_setting("bind_mode", "localhost"),
            **extra,
        }

    def guard(request: Request) -> RedirectResponse | None:
        if not require_admin(request.session):
            return redirect("/login")
        return None

    @app.get("/")
    async def home(request: Request) -> RedirectResponse:
        return redirect("/dashboard" if require_admin(request.session) else "/login")

    @app.get("/login")
    async def login_page(request: Request):
        return templates.TemplateResponse(
            request,
            "login.html",
            await context(request),
        )

    @app.post("/login")
    async def login(request: Request, username: str = Form(...), password: str = Form(...)):
        admin = await repository.get_admin()
        if admin and username == admin["username"] and verify_password(password, admin["password_hash"]):
            request.session["is_admin"] = True
            request.session["username"] = username
            return redirect("/dashboard")
        return templates.TemplateResponse(
            request,
            "login.html",
            await context(request, error="Invalid username or password."),
            status_code=400,
        )

    @app.post("/logout")
    async def logout(request: Request):
        request.session.clear()
        return redirect("/login")

    @app.get("/dashboard")
    async def dashboard(request: Request):
        protected = guard(request)
        if protected:
            return protected
        counts = await repository.dashboard_counts()
        devices = await repository.list_devices()
        alerts = await repository.list_recent_alerts(8)
        active_conditions = await repository.list_active_conditions()
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            await context(
                request,
                counts=counts,
                devices=devices,
                alerts=alerts,
                active_conditions=active_conditions,
            ),
        )

    @app.get("/settings/password")
    async def password_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        return templates.TemplateResponse(
            request,
            "password.html",
            await context(request),
        )

    @app.post("/settings/password")
    async def update_password(
        request: Request,
        current_password: str = Form(...),
        new_password: str = Form(...),
    ):
        protected = guard(request)
        if protected:
            return protected
        admin = await repository.get_admin()
        if not admin or not verify_password(current_password, admin["password_hash"]):
            return templates.TemplateResponse(
                request,
                "password.html",
                await context(request, error="Current password is incorrect."),
                status_code=400,
            )
        await repository.update_password(hash_password(new_password))
        return templates.TemplateResponse(
            request,
            "password.html",
            await context(request, success="Password updated."),
        )

    @app.get("/devices")
    async def devices_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        devices = await repository.list_devices()
        return templates.TemplateResponse(
            request,
            "devices.html",
            await context(request, devices=devices),
        )

    @app.post("/devices/discover")
    async def discover_devices(request: Request):
        protected = guard(request)
        if protected:
            return protected
        await monitor.discover_devices()
        return redirect("/devices")

    @app.post("/devices/{device_id}/update")
    async def update_device(
        request: Request,
        device_id: int,
        display_name: str = Form(...),
        poll_interval_seconds: int = Form(...),
        battery_low_pct_threshold: float = Form(...),
        runtime_low_threshold_seconds: float = Form(...),
    ):
        protected = guard(request)
        if protected:
            return protected
        await repository.update_device_settings(
            device_id,
            display_name,
            bool(device["enabled"]) if device else False,
            poll_interval_seconds,
            battery_low_pct_threshold,
            runtime_low_threshold_seconds,
        )
        return redirect("/devices")

    @app.post("/devices/{device_id}/toggle")
    async def toggle_device(request: Request, device_id: int):
        protected = guard(request)
        if protected:
            return protected
        device = await repository.get_device(device_id)
        if device:
            await repository.set_device_enabled(device_id, not bool(device["enabled"]))
        return redirect("/devices")

    @app.get("/services")
    async def services_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        service_type = request.query_params.get("service_type", "email")
        services = await repository.list_services()
        return templates.TemplateResponse(
            request,
            "services.html",
            await context(
                request,
                services=services,
                service_type=service_type,
                service_fields=service_type_fields(service_type),
            ),
        )

    @app.post("/services/new")
    async def create_service(request: Request):
        protected = guard(request)
        if protected:
            return protected
        form = dict(await request.form())
        service_type = str(form["service_type"])
        await repository.create_service(
            service_type,
            str(form["name"]),
            parse_service_config(service_type, form),
        )
        return redirect("/services")

    @app.get("/channels")
    async def channels_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        services = await repository.list_services()
        channels = await repository.list_channels()
        selected_type = request.query_params.get(
            "service_type",
            services[0]["service_type"] if services else "email",
        )
        return templates.TemplateResponse(
            request,
            "channels.html",
            await context(
                request,
                services=services,
                channels=channels,
                service_type=selected_type,
                target_fields=channel_target_fields(selected_type),
            ),
        )

    @app.post("/channels/new")
    async def create_channel(request: Request):
        protected = guard(request)
        if protected:
            return protected
        form = dict(await request.form())
        service_id = int(form["service_id"])
        services = await repository.list_services()
        service = next(item for item in services if int(item["id"]) == service_id)
        await repository.create_channel(
            str(form["name"]),
            service_id,
            parse_channel_target(service["service_type"], form),
            str(form.get("extra_text", "")),
        )
        return redirect("/channels")

    @app.get("/rules")
    async def rules_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        devices = await repository.list_devices()
        channels = await repository.list_channels()
        rules = await repository.list_rules()
        return templates.TemplateResponse(
            request,
            "rules.html",
            await context(request, devices=devices, channels=channels, rules=rules),
        )

    @app.post("/rules/new")
    async def create_rule(
        request: Request,
        ups_device_id: int = Form(...),
        condition_key: str = Form(...),
        channel_id: int = Form(...),
        repeat_interval_seconds: int = Form(900),
        send_recovery: str | None = Form(None),
    ):
        protected = guard(request)
        if protected:
            return protected
        await repository.create_rule(
            ups_device_id,
            condition_key,
            channel_id,
            repeat_interval_seconds,
            send_recovery == "on",
        )
        return redirect("/rules")

    @app.get("/history")
    async def history_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        alerts = await repository.list_recent_alerts(200)
        return templates.TemplateResponse(
            request,
            "history.html",
            await context(request, alerts=alerts),
        )

    @app.get("/graphs")
    async def graphs_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        devices = await repository.list_devices()
        graph_cards: list[dict[str, Any]] = []
        for device in devices:
            samples = await repository.recent_samples_for_device(device["id"])
            graph_cards.append(
                {
                    "device": device,
                    "samples": samples,
                    "battery_points": build_graph_points(samples, "battery_charge"),
                    "runtime_points": build_graph_points(samples, "runtime_seconds"),
                    "load_points": build_graph_points(samples, "load_percent"),
                }
            )
        return templates.TemplateResponse(
            request,
            "graphs.html",
            await context(request, graph_cards=graph_cards),
        )

    @app.get("/diagnostics")
    async def diagnostics_page(request: Request):
        protected = guard(request)
        if protected:
            return protected
        services = await repository.list_services()
        channels = await repository.list_channels()
        return templates.TemplateResponse(
            request,
            "diagnostics.html",
            await context(request, services=services, channels=channels),
        )

    @app.post("/diagnostics/test")
    async def diagnostics_test(request: Request, channel_id: int = Form(...)):
        protected = guard(request)
        if protected:
            return protected
        channels = await repository.list_channels()
        channel = next(item for item in channels if int(item["id"]) == channel_id)
        result = await monitor.notifier.deliver(
            channel["service_type"],
            channel["service_config"],
            channel["target"],
            "Power Snitch test alert",
            "This is a test alert from Power Snitch diagnostics.",
        )
        services = await repository.list_services()
        return templates.TemplateResponse(
            request,
            "diagnostics.html",
            await context(
                request,
                services=services,
                channels=channels,
                test_result=result,
            ),
        )

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    return app
