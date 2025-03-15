#!/usr/bin/env python3
"""
Power Snitch - UPS Monitoring and Notification System
Monitors UPS status and sends notifications based on configured triggers.
"""

import os
import sys
import time
import logging
import subprocess
import json
import smtplib
import requests
from datetime import datetime, time as dtime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from web.db import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/power_snitch/power_snitch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PowerSnitch:
    def __init__(self, db_path):
        """Initialize Power Snitch with database connection."""
        self.db = Database(db_path)
        self.setup_notification_services()
        self.last_notification = {}
        self.last_battery_level = None
        self.last_runtime = None
        self.last_status = None
        
    def setup_notification_services(self):
        """Set up notification services from database configuration."""
        # Webhook
        webhook_service = self.db.get_notification_service('webhook')
        if webhook_service and webhook_service.enabled:
            webhook_config = webhook_service.webhook_config
            self.webhook_url = webhook_config.url
            self.webhook_method = webhook_config.method
            self.webhook_timeout = webhook_config.timeout
            self.webhook_headers = json.loads(webhook_config.headers) if webhook_config.headers else {}
        else:
            self.webhook_url = None
            self.webhook_method = None
            self.webhook_timeout = None
            self.webhook_headers = None
        
        # Email
        email_service = self.db.get_notification_service('email')
        if email_service and email_service.enabled:
            email_config = email_service.email_config
            self.smtp_host = email_config.smtp_host
            self.smtp_port = email_config.smtp_port
            self.smtp_username = email_config.smtp_username
            self.smtp_password = email_config.smtp_password
            self.smtp_use_tls = email_config.use_tls
            self.email_recipients = [r.email_address for r in email_config.recipients]
        else:
            self.smtp_host = None
            self.smtp_port = None
            self.smtp_username = None
            self.smtp_password = None
            self.smtp_use_tls = None
            self.email_recipients = []
        
        # SMS
        sms_service = self.db.get_notification_service('sms')
        if sms_service and sms_service.enabled:
            sms_config = sms_service.sms_config
            self.twilio_sid = sms_config.twilio_account_sid
            self.twilio_token = sms_config.twilio_auth_token
            self.twilio_from = sms_config.twilio_from_number
            self.sms_recipients = [r.phone_number for r in sms_config.recipients]
            self.twilio_client = Client(self.twilio_sid, self.twilio_token)
        else:
            self.twilio_sid = None
            self.twilio_token = None
            self.twilio_from = None
            self.sms_recipients = []
            self.twilio_client = None
    
    def get_ups_status(self):
        """Get current UPS status using NUT."""
        try:
            ups_config = self.db.get_ups_config()
            result = subprocess.run(['upsc', ups_config.name], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to get UPS status: {result.stderr}")
                return None
            
            status = {}
            for line in result.stdout.splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    status[key.strip()] = value.strip()
            
            return status
        except Exception as e:
            logger.error(f"Error getting UPS status: {str(e)}")
            return None
    
    def check_battery_health(self, status):
        """Check battery health and record metrics."""
        try:
            battery_config = self.db.get_battery_health_config()
            if not battery_config:
                return
            
            # Extract battery metrics
            metrics = {
                'charge_percentage': int(status.get('battery.charge', 0)),
                'runtime_seconds': int(status.get('battery.runtime', 0)),
                'voltage': float(status.get('battery.voltage', 0)),
                'current': float(status.get('battery.current', 0)),
                'temperature': float(status.get('battery.temperature', 0)),
                'energy_stored': float(status.get('battery.energy', 0)),
                'energy_full': float(status.get('battery.energy.full', 0)),
                'battery_date': status.get('battery.date'),
                'battery_type': status.get('battery.type'),
                'battery_packs': int(status.get('battery.packs', 1)),
                'battery_packs_bad': int(status.get('battery.packs.bad', 0))
            }
            
            # Record battery health history
            self.db.add_battery_health_history(**metrics)
            
            # Check for alerts
            if metrics['charge_percentage'] <= battery_config.low_charge_threshold:
                self.db.add_battery_alert('low_charge', metrics['charge_percentage'], battery_config.low_charge_threshold)
            
            if metrics['runtime_seconds'] <= battery_config.low_runtime_threshold:
                self.db.add_battery_alert('low_runtime', metrics['runtime_seconds'], battery_config.low_runtime_threshold)
            
            if battery_config.low_voltage_threshold and metrics['voltage'] <= battery_config.low_voltage_threshold:
                self.db.add_battery_alert('low_voltage', metrics['voltage'], battery_config.low_voltage_threshold)
            
            if battery_config.high_voltage_threshold and metrics['voltage'] >= battery_config.high_voltage_threshold:
                self.db.add_battery_alert('high_voltage', metrics['voltage'], battery_config.high_voltage_threshold)
            
            if battery_config.temperature_high_threshold and metrics['temperature'] >= battery_config.temperature_high_threshold:
                self.db.add_battery_alert('high_temperature', metrics['temperature'], battery_config.temperature_high_threshold)
            
            if battery_config.temperature_low_threshold and metrics['temperature'] <= battery_config.temperature_low_threshold:
                self.db.add_battery_alert('low_temperature', metrics['temperature'], battery_config.temperature_low_threshold)
            
            if metrics['battery_packs_bad'] > 0:
                self.db.add_battery_alert('bad_battery_packs', metrics['battery_packs_bad'], 0)
        
        except Exception as e:
            logger.error(f"Error checking battery health: {str(e)}")
    
    def check_health_notification(self):
        """Check if daily health notification is due."""
        try:
            health_check = self.db.get_health_check()
            if not health_check or not health_check.enabled:
                return
            
            current_time = datetime.now().time()
            if current_time >= health_check.notification_time:
                # Check if we've already sent a notification today
                if health_check.last_notification:
                    last_notification_date = health_check.last_notification.date()
                    if last_notification_date == datetime.now().date():
                        return
                
                # Get current UPS status
                status = self.get_ups_status()
                if status:
                    self.send_health_notification(status)
                    # Update last notification time
                    self.db.update_health_check(last_notification=datetime.now())
        
        except Exception as e:
            logger.error(f"Error checking health notification: {str(e)}")
    
    def send_health_notification(self, status):
        """Send daily health status notification."""
        try:
            message = "Daily UPS Health Report\n\n"
            message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"Battery Charge: {status.get('battery.charge', 'N/A')}%\n"
            message += f"Runtime: {status.get('battery.runtime', 'N/A')} seconds\n"
            message += f"Temperature: {status.get('battery.temperature', 'N/A')}°C\n"
            message += f"Input Voltage: {status.get('input.voltage', 'N/A')}V\n"
            message += f"Output Voltage: {status.get('output.voltage', 'N/A')}V\n"
            message += f"Load: {status.get('ups.load', 'N/A')}%\n"
            
            # Send notifications through all enabled services
            self.send_webhook(message)
            self.send_email("UPS Daily Health Report", message)
            self.send_sms(message)
            
        except Exception as e:
            logger.error(f"Error sending health notification: {str(e)}")
    
    def check_notifications(self, status):
        """Check if notifications should be sent based on triggers."""
        try:
            triggers = self.db.get_triggers()
            always_notify_events = self.db.get_always_notify_events()
            
            current_time = time.time()
            battery_level = int(status.get('battery.charge', 0))
            runtime = int(status.get('battery.runtime', 0))
            ups_status = status.get('ups.status', '')
            
            # Check battery level triggers
            for trigger in triggers:
                if trigger.trigger_type == 'battery_level':
                    if battery_level <= trigger.value:
                        if (trigger.trigger_type not in self.last_notification or
                            current_time - self.last_notification[trigger.trigger_type] >= 3600):
                            message = f"Battery level is at {battery_level}%"
                            self.send_notifications(message)
                            self.last_notification[trigger.trigger_type] = current_time
            
            # Check runtime triggers
            for trigger in triggers:
                if trigger.trigger_type == 'runtime':
                    if runtime <= trigger.value:
                        if (trigger.trigger_type not in self.last_notification or
                            current_time - self.last_notification[trigger.trigger_type] >= 3600):
                            message = f"UPS runtime is {runtime} seconds"
                            self.send_notifications(message)
                            self.last_notification[trigger.trigger_type] = current_time
            
            # Check status changes
            if self.last_status != ups_status:
                self.last_status = ups_status
                for event in always_notify_events:
                    if event.event_type in ups_status:
                        message = f"UPS status changed to: {ups_status}"
                        self.send_notifications(message)
            
            # Check battery level changes
            if self.last_battery_level is not None:
                battery_diff = abs(battery_level - self.last_battery_level)
                if battery_diff >= 10:
                    message = f"Battery level changed by {battery_diff}%"
                    self.send_notifications(message)
            self.last_battery_level = battery_level
            
            # Check runtime changes
            if self.last_runtime is not None:
                runtime_diff = abs(runtime - self.last_runtime)
                if runtime_diff >= 300:
                    message = f"Runtime changed by {runtime_diff} seconds"
                    self.send_notifications(message)
            self.last_runtime = runtime
            
        except Exception as e:
            logger.error(f"Error checking notifications: {str(e)}")
    
    def send_notifications(self, message):
        """Send notifications through all enabled services."""
        self.send_webhook(message)
        self.send_email("UPS Status Update", message)
        self.send_sms(message)
    
    def send_webhook(self, message):
        """Send webhook notification."""
        if not self.webhook_url:
            return
        
        try:
            payload = {
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.webhook_headers,
                timeout=self.webhook_timeout
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error sending webhook: {str(e)}")
    
    def send_email(self, subject, message):
        """Send email notification."""
        if not self.email_recipients:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = ', '.join(self.email_recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
    
    def send_sms(self, message):
        """Send SMS notification."""
        if not self.sms_recipients:
            return
        
        try:
            for recipient in self.sms_recipients:
                self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_from,
                    to=recipient
                )
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Starting Power Snitch monitoring...")
        
        while True:
            try:
                # Get UPS status
                status = self.get_ups_status()
                if status:
                    # Check battery health
                    self.check_battery_health(status)
                    
                    # Check notifications
                    self.check_notifications(status)
                    
                    # Check health notification
                    self.check_health_notification()
                
                # Sleep for configured interval
                ups_config = self.db.get_ups_config()
                
                time.sleep(ups_config.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down Power Snitch...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying

def main():
    """Main entry point."""
    try:
        # Ensure log directory exists
        os.makedirs('/var/log/power_snitch', exist_ok=True)
        
        # Initialize database
        db_path = '/opt/power_snitch/data/power_snitch.db'
        db = Database(db_path)
        db.init_db()
        
        # Create and run Power Snitch
        snitch = PowerSnitch(db_path)
        snitch.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 