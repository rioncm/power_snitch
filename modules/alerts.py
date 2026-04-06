import aiohttp
import aiosmtplib
from email.message import EmailMessage
from typing import Dict, Any
from modules.config import AlertRule, SMTPConfig, Channel
from modules.models import log_alert_event

async def dispatch_alert(alert: AlertRule, status: Dict[str, Any], channels: Dict[str, Channel], smtp_config: SMTPConfig):
    for method_key in alert.methods:
        channel = channels[method_key]
        if channel.type == "webhook" and hasattr(channel, "url") and isinstance(channel.url, str):
            await send_webhook(channel, alert.event, status)
        elif channel.type == "email" and hasattr(channel, "to"):
            await send_email(channel, alert.event, status, smtp_config)

async def send_webhook(channel: Channel, event: str, status: Dict[str, Any]):
    try:
        async with aiohttp.ClientSession() as session:
            headers = getattr(channel, "headers", {}) or {}
            url = str(getattr(channel, "url", ""))
            async with session.post(url, json=status, headers=headers) as response:
                success = 200 <= response.status < 300
                await log_alert_event("webhook", url, event, success, response.status)
    except Exception as e:
        url = str(getattr(channel, "url", ""))
        await log_alert_event("webhook", url, event, False, error_message=str(e))

async def send_email(channel: Channel, event: str, status: Dict[str, Any], smtp_config: SMTPConfig):
    if not hasattr(channel, "type") or channel.type != "email":
        raise ValueError("send_email called with a non-email channel.")

    if not hasattr(channel, "to") or not isinstance(channel.to, list):
        raise ValueError("Email channel must have a 'to' field that is a list of email addresses.")

    if not smtp_config or not all(hasattr(smtp_config, attr) for attr in ["server", "port", "username", "password"]):
        raise ValueError("SMTP configuration is incomplete.")

    if not all(isinstance(email, str) for email in channel.to):
        raise ValueError("All recipients in 'to' must be strings.")

    if not isinstance(smtp_config.port, int):
        raise ValueError("SMTP port must be an integer.")

    if not isinstance(smtp_config.server, str) or not isinstance(smtp_config.username, str) or not isinstance(smtp_config.password, str):
        raise ValueError("SMTP server, username, and password must be strings.")
    try:
        message = EmailMessage()
        message["From"] = smtp_config.username
        message["To"] = ", ".join(channel.to)
        message["Subject"] = f"UPS Alert: {event}"
        message.set_content(
            f"Event: {event}\nTime: {status['timestamp']}\nStatus: {status['ups_status']}\nBattery: {status['battery_charge']}%\nVoltage: {status['voltage']}\nRuntime: {status['runtime_estimate']}s"
        )

        await aiosmtplib.send(
            message,
            hostname=smtp_config.server,
            port=smtp_config.port,
            username=smtp_config.username,
            password=smtp_config.password,
            start_tls=True
        )
        await log_alert_event("email", ",".join(channel.to), event, True)
    except Exception as e:
        await log_alert_event("email", ",".join(channel.to), event, False, error_message=str(e))
