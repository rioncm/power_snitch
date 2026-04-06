from __future__ import annotations

from email.message import EmailMessage
from typing import Any

import aiohttp
import aiosmtplib

from powersnitch_app.models import DeliveryResult


class NotificationDispatcher:
    async def deliver(
        self,
        service_type: str,
        service_config: dict[str, Any],
        target: dict[str, Any],
        subject: str,
        body: str,
    ) -> DeliveryResult:
        if service_type == "email":
            return await self._send_email(service_config, target, subject, body)
        if service_type == "telegram":
            return await self._send_telegram(service_config, target, body)
        if service_type == "twilio":
            return await self._send_twilio(service_config, target, body)
        if service_type == "webhook":
            return await self._send_webhook(service_config, target, subject, body)
        return DeliveryResult(service_type, "unknown", False, error_message="unsupported service")

    async def _send_email(
        self,
        service_config: dict[str, Any],
        target: dict[str, Any],
        subject: str,
        body: str,
    ) -> DeliveryResult:
        recipients = [item.strip() for item in target.get("to", "").split(",") if item.strip()]
        message = EmailMessage()
        message["From"] = service_config.get("from_email") or service_config.get("username")
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(body)
        try:
            await aiosmtplib.send(
                message,
                hostname=service_config["host"],
                port=int(service_config.get("port", 587)),
                username=service_config.get("username"),
                password=service_config.get("password"),
                start_tls=bool(service_config.get("start_tls", True)),
            )
            return DeliveryResult("email", ",".join(recipients), True)
        except Exception as exc:
            return DeliveryResult("email", ",".join(recipients), False, error_message=str(exc))

    async def _send_telegram(
        self,
        service_config: dict[str, Any],
        target: dict[str, Any],
        body: str,
    ) -> DeliveryResult:
        token = service_config.get("bot_token", "")
        chat_id = target.get("chat_id", "")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.post(url, json={"chat_id": chat_id, "text": body})
                ok = 200 <= response.status < 300
                return DeliveryResult("telegram", str(chat_id), ok, response.status)
            except Exception as exc:
                return DeliveryResult("telegram", str(chat_id), False, error_message=str(exc))

    async def _send_twilio(
        self,
        service_config: dict[str, Any],
        target: dict[str, Any],
        body: str,
    ) -> DeliveryResult:
        account_sid = service_config.get("account_sid", "")
        auth_token = service_config.get("auth_token", "")
        from_number = service_config.get("from_number", "")
        to_number = target.get("to_number", "")
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        async with aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(account_sid, auth_token)
        ) as session:
            try:
                response = await session.post(
                    url,
                    data={"From": from_number, "To": to_number, "Body": body},
                )
                ok = 200 <= response.status < 300
                return DeliveryResult("twilio", str(to_number), ok, response.status)
            except Exception as exc:
                return DeliveryResult("twilio", str(to_number), False, error_message=str(exc))

    async def _send_webhook(
        self,
        service_config: dict[str, Any],
        target: dict[str, Any],
        subject: str,
        body: str,
    ) -> DeliveryResult:
        url = target.get("url") or service_config.get("url", "")
        headers = service_config.get("headers", {})
        payload = {"subject": subject, "message": body}
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.post(url, json=payload, headers=headers)
                ok = 200 <= response.status < 300
                return DeliveryResult("webhook", url, ok, response.status)
            except Exception as exc:
                return DeliveryResult("webhook", url, False, error_message=str(exc))

