import aiohttp
import aiosmtplib
from email.message import EmailMessage
from typing import Dict, Any
from modules.config import AlertRule, SMTPConfig, Channel
from modules.models import log_alert_event

async def dispatch_alert(alert: AlertRule, status: Dict[str, Any], channels: Dict[str, Channel], smtp_config: SMTPConfig):
    for method_key in alert.methods:
        channel = channels[method_key]
        if channel.type == "webhook":
            await send_webhook(channel, alert.event, status)
        elif channel.type == "email":
            await send_email(channel, alert.event, status, smtp_config)

async def send_webhook(channel: Channel, event: str, status: Dict[str, Any]):
    try:
        async with aiohttp.ClientSession() as session:
            headers = channel.headers or {}
            async with session.post(channel.url, json=status, headers=headers) as response:
                success = 200 <= response.status < 300
                await log_alert_event("webhook", channel.url, event, success, response.status)
    except Exception as e:
        await log_alert_event("webhook", channel.url, event, False, error_message=str(e))

async def send_email(channel: Channel, event: str, status: Dict[str, Any], smtp_config: SMTPConfig):
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
