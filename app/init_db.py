#!/usr/bin/env python3
"""
Power Snitch Database Initialization Script
Creates the database and loads default settings.
"""

import os
import sys
import logging
from datetime import datetime, time
from ..db import Database, WebInterface, UPSConfig, HealthCheck, BatteryHealthConfig, NotificationService, WebhookConfig, EmailConfig, EmailRecipient, SMSConfig, SMSRecipient, Trigger, AlwaysNotifyEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/power_snitch/init_db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_database(db_path):
    """Initialize database with default settings."""
    try:
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        db = Database(db_path)
        db.init_db()
        
        # Create web interface settings
        web_interface = WebInterface(
            port=80,
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyDAXxZxXh5K2',  # 'password'
            setup_completed=False
        )
        db.get_session().add(web_interface)
        
        # Create UPS configuration
        ups_config = UPSConfig(
            name='ups',
            description='Default UPS',
            poll_interval=5
        )
        db.get_session().add(ups_config)
        
        # Create health check settings
        health_check = HealthCheck(
            enabled=False,
            notification_time=time(9, 0)  # 9:00 AM
        )
        db.get_session().add(health_check)
        
        # Create battery health configuration
        battery_config = BatteryHealthConfig(
            low_charge_threshold=20,
            warning_charge_threshold=50,
            low_runtime_threshold=300,
            low_voltage_threshold=None,
            high_voltage_threshold=None,
            temperature_high_threshold=None,
            temperature_low_threshold=None
        )
        db.get_session().add(battery_config)
        
        # Create notification services
        # Webhook
        webhook_service = NotificationService(service_type='webhook', enabled=False)
        db.get_session().add(webhook_service)
        db.get_session().flush()
        
        webhook_config = WebhookConfig(
            service_id=webhook_service.id,
            url='http://localhost/webhook',
            method='POST',
            timeout=10,
            headers='{}'
        )
        db.get_session().add(webhook_config)
        
        # Email
        email_service = NotificationService(service_type='email', enabled=False)
        db.get_session().add(email_service)
        db.get_session().flush()
        
        email_config = EmailConfig(
            service_id=email_service.id,
            smtp_host='smtp.example.com',
            smtp_port=587,
            smtp_username='user@example.com',
            smtp_password='password',
            use_tls=True
        )
        db.get_session().add(email_config)
        db.get_session().flush()
        
        email_recipient = EmailRecipient(
            email_config_id=email_config.id,
            email_address='admin@example.com'
        )
        db.get_session().add(email_recipient)
        
        # SMS
        sms_service = NotificationService(service_type='sms', enabled=False)
        db.get_session().add(sms_service)
        db.get_session().flush()
        
        sms_config = SMSConfig(
            service_id=sms_service.id,
            twilio_account_sid='your_account_sid',
            twilio_auth_token='your_auth_token',
            twilio_from_number='+1234567890'
        )
        db.get_session().add(sms_config)
        db.get_session().flush()
        
        sms_recipient = SMSRecipient(
            sms_config_id=sms_config.id,
            phone_number='+1234567890'
        )
        db.get_session().add(sms_recipient)
        
        # Create default triggers
        triggers = [
            Trigger(trigger_type='battery_level', value=20),
            Trigger(trigger_type='battery_level', value=50),
            Trigger(trigger_type='runtime', value=300)
        ]
        for trigger in triggers:
            db.get_session().add(trigger)
        
        # Create default always notify events
        events = [
            AlwaysNotifyEvent(trigger_id=triggers[0].id, event_type='low_battery'),
            AlwaysNotifyEvent(trigger_id=triggers[1].id, event_type='warning_battery'),
            AlwaysNotifyEvent(trigger_id=triggers[2].id, event_type='low_runtime')
        ]
        for event in events:
            db.get_session().add(event)
        
        # Commit all changes
        db.get_session().commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        db.get_session().rollback()
        raise

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: init_db.py <db_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    init_database(db_path)

if __name__ == '__main__':
    main() 