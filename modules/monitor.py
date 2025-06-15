import asyncio
import subprocess
import json
import time
from datetime import datetime
from modules.config import PowerSnitchConfig
from modules.logger import get_logger
from modules.models import log_poll_event, get_last_alert_time, update_alert_time
from modules.alerts import dispatch_alert

class Monitor:
    def __init__(self, config: PowerSnitchConfig):
        self.config = config
        self.logger = get_logger(config.logging)
        self.last_alerts = {}  # Tracks last alert timestamps by event name

    def get_ups_status(self):
        try:
            result = subprocess.run(
                self.config.ups.status_command.split(),
                capture_output=True, text=True, check=True
            )
            return self.parse_upsc_output(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get UPS status: {e.stderr.strip()}")
            return {"event_type": "error", "ups_status": "ERROR"}

    def parse_upsc_output(self, raw_output):
        status = {}
        for line in raw_output.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                status[key.strip()] = value.strip()

        # Basic fields, adapt keys as needed from NUT
        parsed = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "status_poll",
            "voltage": float(status.get("input.voltage", 0)),
            "battery_charge": float(status.get("battery.charge", 0)),
            "runtime_estimate": float(status.get("battery.runtime", 0)),
            "ups_status": status.get("ups.status", "UNKNOWN"),
            "raw_json": json.dumps(status)
        }
        return parsed

    async def monitor_loop(self):
        poll_interval = self.config.ups.poll_interval_seconds
        while True:
            status = self.get_ups_status()
            await log_poll_event(status)

            for alert in self.config.alerts:
                if self.should_trigger(alert.event, status["ups_status"]):
                    now = time.time()
                    last_sent = self.last_alerts.get(alert.event, 0)
                    if not alert.repeat_interval_seconds or now - last_sent >= alert.repeat_interval_seconds:
                        await dispatch_alert(alert, status, self.config.channels, self.config.smtp)
                        self.last_alerts[alert.event] = now

            await asyncio.sleep(poll_interval)

    def should_trigger(self, pattern: str, ups_status: str) -> bool:
        return re.search(pattern, ups_status or "") is not None
