#!/usr/bin/env python3

import os
import time
import json
import logging
from logging.handlers import RotatingFileHandler
import smtplib
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
from twilio.rest import Client
from nut2 import PyNUTClient
import threading
from web_app import start_web_interface

# Configure logging
def setup_logging():
    log_dir = '/var/log/power_snitch'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'power_snitch.log')
    max_bytes = 10 * 1024 * 1024  # 10MB
    backup_count = 5  # Keep 5 backup files

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Set up rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

class NotificationManager:
    def __init__(self, config):
        self.config = config
        self.setup_notification_services()

    def setup_notification_services(self):
        """Initialize notification services based on configuration."""
        self.webhook_enabled = self.config['webhook']['enabled']
        self.email_enabled = self.config['email']['enabled']
        self.sms_enabled = self.config['sms']['enabled']

        # Setup Twilio client if SMS is enabled
        if self.sms_enabled:
            twilio_config = self.config['sms']['twilio']
            self.twilio_client = Client(
                twilio_config['account_sid'],
                twilio_config['auth_token']
            )

    def format_message(self, event_type, status):
        """Format a human-readable message for email and SMS."""
        message = f"UPS Event: {event_type}\n"
        message += f"Time: {datetime.utcnow().isoformat()}Z\n"
        message += f"Battery Level: {status['battery_level']}%\n"
        message += f"Load: {status['load_percentage']}%\n"
        message += f"Runtime Remaining: {status['runtime_remaining']} seconds\n"
        message += f"On Battery: {'Yes' if status['on_battery'] else 'No'}"
        return message

    def send_webhook(self, event_type, status):
        """Send notification via webhook."""
        if not self.webhook_enabled:
            return

        webhook_config = self.config['webhook']
        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": status
        }

        try:
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config.get('headers', {}),
                timeout=webhook_config.get('timeout', 10)
            )
            response.raise_for_status()
            logger.info(f"Successfully sent webhook notification: {event_type}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook notification: {e}")

    def send_email(self, event_type, status):
        """Send notification via email."""
        if not self.email_enabled:
            return

        email_config = self.config['email']
        smtp_config = email_config['smtp']

        message = MIMEMultipart()
        message["Subject"] = f"UPS Alert: {event_type}"
        message["From"] = smtp_config['username']

        body = self.format_message(event_type, status)
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                if smtp_config['use_tls']:
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                
                for recipient in email_config['recipients']:
                    message["To"] = recipient
                    server.send_message(message)
                    logger.info(f"Successfully sent email notification to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def send_sms(self, event_type, status):
        """Send notification via SMS using Twilio."""
        if not self.sms_enabled:
            return

        sms_config = self.config['sms']
        twilio_config = sms_config['twilio']
        message_body = self.format_message(event_type, status)

        try:
            for recipient in sms_config['recipients']:
                self.twilio_client.messages.create(
                    body=message_body,
                    from_=twilio_config['from_number'],
                    to=recipient
                )
                logger.info(f"Successfully sent SMS notification to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")

    def notify_all(self, event_type, status):
        """Send notifications through all enabled channels."""
        self.send_webhook(event_type, status)
        self.send_email(event_type, status)
        self.send_sms(event_type, status)

class UPSMonitor:
    def __init__(self, config):
        self.config = config
        self.client = PyNUTClient()
        self.previous_status = None
        self.notification_manager = NotificationManager(config)
        self.connection_retry_count = 0
        self.max_retries = 5
        self.retry_delay = 60  # seconds
        self.ups_status = {
            "connected": False,
            "error": None,
            "last_successful_check": None
        }
        
    def verify_ups_connection(self):
        """Verify that the UPS is connected and accessible."""
        try:
            ups_list = self.client.list_ups()
            if not ups_list or self.config['ups']['name'] not in ups_list:
                raise ValueError(f"UPS '{self.config['ups']['name']}' not found. Available UPS devices: {list(ups_list.keys())}")
            return True
        except Exception as e:
            self.ups_status["error"] = str(e)
            return False

    def update_connection_status(self, connected, error=None):
        """Update the UPS connection status."""
        self.ups_status["connected"] = connected
        self.ups_status["error"] = error
        if connected:
            self.ups_status["last_successful_check"] = datetime.utcnow().isoformat() + "Z"
            self.connection_retry_count = 0
        self.save_status()

    def save_status(self):
        """Save current status to file for web interface."""
        try:
            with open('status.json', 'w') as f:
                json.dump({
                    'status': self.previous_status if self.previous_status else {},
                    'notifications': {
                        'webhook': self.config['notifications']['webhook']['enabled'],
                        'email': self.config['notifications']['email']['enabled'],
                        'sms': self.config['notifications']['sms']['enabled']
                    },
                    'ups_status': self.ups_status
                }, f)
        except Exception as e:
            logger.error(f"Error saving status file: {e}")
        
    def get_ups_status(self):
        """Get current UPS status."""
        if not self.verify_ups_connection():
            if self.connection_retry_count >= self.max_retries:
                logger.error(f"Failed to connect to UPS after {self.max_retries} attempts. Waiting {self.retry_delay} seconds before next retry.")
                time.sleep(self.retry_delay)
                self.connection_retry_count = 0
            else:
                self.connection_retry_count += 1
                logger.warning(f"UPS connection attempt {self.connection_retry_count} of {self.max_retries} failed")
            
            self.update_connection_status(False, self.ups_status["error"])
            return None

        try:
            vars = self.client.list_vars(self.config['ups']['name'])
            if not vars:
                raise ValueError("No data received from UPS")

            required_vars = ['ups.status', 'battery.charge', 'battery.runtime', 'ups.load']
            missing_vars = [var for var in required_vars if var not in vars]
            if missing_vars:
                raise ValueError(f"Missing required UPS variables: {missing_vars}")

            status = {
                "on_battery": vars.get("ups.status", "").lower().find("onbatt") != -1,
                "battery_level": float(vars.get("battery.charge", "0")),
                "runtime_remaining": int(vars.get("battery.runtime", "0")),
                "load_percentage": float(vars.get("ups.load", "0"))
            }
            
            self.update_connection_status(True)
            return status

        except ValueError as e:
            logger.error(f"UPS data error: {e}")
            self.update_connection_status(False, str(e))
            return None
        except Exception as e:
            logger.error(f"Error getting UPS status: {e}")
            self.update_connection_status(False, str(e))
            return None

    def should_send_notification(self, current_status):
        """Determine if we should send a notification based on status changes and triggers."""
        if not self.previous_status:
            return True

        try:
            triggers = self.config['triggers']
            
            # Check for power state changes
            if current_status["on_battery"] != self.previous_status["on_battery"]:
                return True

            # Check for significant battery level changes
            if abs(current_status["battery_level"] - self.previous_status["battery_level"]) >= triggers['battery_level_change']:
                return True

            # Check for significant load changes
            if abs(current_status["load_percentage"] - self.previous_status["load_percentage"]) >= triggers['load_change']:
                return True

            # Check for low battery condition
            if current_status["battery_level"] <= 20 and "low_battery" in triggers['always_notify']:
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking notification triggers: {e}")
            return False

    def determine_event_type(self, status):
        """Determine the type of event based on status."""
        try:
            if status["on_battery"]:
                return "power_failure"
            elif self.previous_status and self.previous_status["on_battery"] and not status["on_battery"]:
                return "power_restored"
            elif status["battery_level"] <= 20:
                return "low_battery"
            return "status_update"
        except Exception as e:
            logger.error(f"Error determining event type: {e}")
            return "status_update"

    def run(self):
        """Main monitoring loop."""
        logger.info("Starting UPS monitoring service...")
        
        while True:
            try:
                current_status = self.get_ups_status()
                
                if current_status:
                    if self.should_send_notification(current_status):
                        event_type = self.determine_event_type(current_status)
                        self.notification_manager.notify_all(event_type, current_status)
                        self.previous_status = current_status
                else:
                    # If we lost connection and were previously connected, send a notification
                    if self.previous_status and self.ups_status["error"]:
                        self.notification_manager.notify_all("ups_error", {
                            "error": self.ups_status["error"],
                            "last_known_status": self.previous_status
                        })
                
                time.sleep(self.config['ups']['poll_interval'])
                
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                self.update_connection_status(False, str(e))
                time.sleep(self.config['ups']['poll_interval'])

def load_config():
    """Load configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

def main():
    # Load configuration
    config = load_config()
    
    # Start web interface in a separate thread
    web_thread = threading.Thread(target=start_web_interface)
    web_thread.daemon = True
    web_thread.start()
    
    # Start UPS monitoring
    monitor = UPSMonitor(config)
    monitor.run()

if __name__ == "__main__":
    main() 