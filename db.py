#!/usr/bin/env python3
"""
Power Snitch Database Module
Handles all database operations using SQLAlchemy.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Time, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import json
import logging

# Create base class for declarative models
Base = declarative_base()

# Database Models
class WebInterface(Base):
    __tablename__ = 'web_interface'
    
    id = Column(Integer, primary_key=True)
    port = Column(Integer, nullable=False, default=80)
    password_hash = Column(String, nullable=False)
    setup_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UPSConfig(Base):
    __tablename__ = 'ups_config'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    poll_interval = Column(Integer, nullable=False, default=5)
    # NUT-specific fields
    nut_device_name = Column(String, nullable=False, default='ups')
    nut_driver = Column(String, nullable=False, default='usbhid-ups')
    nut_port = Column(String)
    nut_username = Column(String, nullable=False, default='admin')
    nut_password = Column(String, nullable=False)
    nut_retry_count = Column(Integer, default=3)
    nut_retry_delay = Column(Integer, default=5)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class HealthCheck(Base):
    __tablename__ = 'health_check'
    
    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, nullable=False, default=False)
    notification_time = Column(Time, nullable=False)
    last_notification = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BatteryHealthConfig(Base):
    __tablename__ = 'battery_health_config'
    
    id = Column(Integer, primary_key=True)
    low_charge_threshold = Column(Integer, nullable=False, default=20)
    warning_charge_threshold = Column(Integer, nullable=False, default=50)
    low_runtime_threshold = Column(Integer, nullable=False, default=300)
    low_voltage_threshold = Column(Float)
    high_voltage_threshold = Column(Float)
    temperature_high_threshold = Column(Float)
    temperature_low_threshold = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BatteryHealthHistory(Base):
    __tablename__ = 'battery_health_history'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    charge_percentage = Column(Integer, nullable=False)
    runtime_seconds = Column(Integer)
    voltage = Column(Float)
    current = Column(Float)
    temperature = Column(Float)
    energy_stored = Column(Float)
    energy_full = Column(Float)
    battery_date = Column(String)
    battery_type = Column(String)
    battery_packs = Column(Integer)
    battery_packs_bad = Column(Integer)
    created_at = Column(DateTime, default=func.now())

class BatteryAlert(Base):
    __tablename__ = 'battery_alerts'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    alert_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class NotificationService(Base):
    __tablename__ = 'notification_services'
    
    id = Column(Integer, primary_key=True)
    service_type = Column(String, nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    webhook_config = relationship("WebhookConfig", back_populates="service", uselist=False)
    email_config = relationship("EmailConfig", back_populates="service", uselist=False)
    sms_config = relationship("SMSConfig", back_populates="service", uselist=False)

class WebhookConfig(Base):
    __tablename__ = 'webhook_config'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('notification_services.id'), nullable=False)
    url = Column(String, nullable=False)
    method = Column(String, nullable=False, default='POST')
    timeout = Column(Integer, nullable=False, default=10)
    headers = Column(Text)  # JSON string of headers
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    service = relationship("NotificationService", back_populates="webhook_config")

class EmailConfig(Base):
    __tablename__ = 'email_config'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('notification_services.id'), nullable=False)
    smtp_host = Column(String, nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_username = Column(String, nullable=False)
    smtp_password = Column(String, nullable=False)
    use_tls = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    service = relationship("NotificationService", back_populates="email_config")
    recipients = relationship("EmailRecipient", back_populates="email_config")

class EmailRecipient(Base):
    __tablename__ = 'email_recipients'
    
    id = Column(Integer, primary_key=True)
    email_config_id = Column(Integer, ForeignKey('email_config.id'), nullable=False)
    email_address = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    email_config = relationship("EmailConfig", back_populates="recipients")

class SMSConfig(Base):
    __tablename__ = 'sms_config'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('notification_services.id'), nullable=False)
    twilio_account_sid = Column(String, nullable=False)
    twilio_auth_token = Column(String, nullable=False)
    twilio_from_number = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    service = relationship("NotificationService", back_populates="sms_config")
    recipients = relationship("SMSRecipient", back_populates="sms_config")

class SMSRecipient(Base):
    __tablename__ = 'sms_recipients'
    
    id = Column(Integer, primary_key=True)
    sms_config_id = Column(Integer, ForeignKey('sms_config.id'), nullable=False)
    phone_number = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    sms_config = relationship("SMSConfig", back_populates="recipients")

class Trigger(Base):
    __tablename__ = 'triggers'
    
    id = Column(Integer, primary_key=True)
    trigger_type = Column(String, nullable=False)
    value = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AlwaysNotifyEvent(Base):
    __tablename__ = 'always_notify_events'
    
    id = Column(Integer, primary_key=True)
    trigger_id = Column(Integer, ForeignKey('triggers.id'), nullable=False)
    event_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    trigger = relationship("Trigger")

class Database:
    def __init__(self, db_path):
        """Initialize database connection."""
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    def init_db(self):
        """Initialize database tables."""
        Base.metadata.create_all(self.engine)
    
    def get_web_interface(self):
        """Get web interface settings."""
        session = self.get_session()
        try:
            return session.query(WebInterface).first()
        finally:
            session.close()
    
    def get_ups_config(self):
        """Get UPS configuration."""
        session = self.get_session()
        try:
            return session.query(UPSConfig).first()
        finally:
            session.close()
    
    def get_health_check(self):
        """Get health check settings."""
        session = self.get_session()
        try:
            return session.query(HealthCheck).first()
        finally:
            session.close()
    
    def get_battery_health_config(self):
        """Get battery health configuration."""
        session = self.get_session()
        try:
            return session.query(BatteryHealthConfig).first()
        finally:
            session.close()
    
    def get_notification_service(self, service_type):
        """Get notification service configuration."""
        session = self.get_session()
        try:
            return session.query(NotificationService).filter_by(service_type=service_type).first()
        finally:
            session.close()
    
    def get_triggers(self):
        """Get all notification triggers."""
        session = self.get_session()
        try:
            return session.query(Trigger).all()
        finally:
            session.close()
    
    def get_always_notify_events(self):
        """Get all always notify events."""
        session = self.get_session()
        try:
            return session.query(AlwaysNotifyEvent).all()
        finally:
            session.close()
    
    def update_web_interface(self, port=None, password_hash=None, setup_completed=None):
        """Update web interface settings."""
        session = self.get_session()
        try:
            web_interface = session.query(WebInterface).first()
            if web_interface:
                if port is not None:
                    web_interface.port = port
                if password_hash is not None:
                    web_interface.password_hash = password_hash
                if setup_completed is not None:
                    web_interface.setup_completed = setup_completed
                session.commit()
            else:
                web_interface = WebInterface(
                    port=port or 8080,
                    password_hash=password_hash or '',
                    setup_completed=setup_completed or False
                )
                session.add(web_interface)
                session.commit()
        finally:
            session.close()
    
    def update_ups_config(self, name=None, description=None, poll_interval=None, 
                         nut_device_name=None, nut_driver=None, nut_port=None,
                         nut_username=None, nut_password=None, nut_retry_count=None,
                         nut_retry_delay=None):
        """Update UPS configuration."""
        session = self.get_session()
        try:
            ups_config = session.query(UPSConfig).first()
            if ups_config:
                if name is not None:
                    ups_config.name = name
                if description is not None:
                    ups_config.description = description
                if poll_interval is not None:
                    ups_config.poll_interval = poll_interval
                if nut_device_name is not None:
                    ups_config.nut_device_name = nut_device_name
                if nut_driver is not None:
                    ups_config.nut_driver = nut_driver
                if nut_port is not None:
                    ups_config.nut_port = nut_port
                if nut_username is not None:
                    ups_config.nut_username = nut_username
                if nut_password is not None:
                    ups_config.nut_password = nut_password
                if nut_retry_count is not None:
                    ups_config.nut_retry_count = nut_retry_count
                if nut_retry_delay is not None:
                    ups_config.nut_retry_delay = nut_retry_delay
                session.commit()
            else:
                ups_config = UPSConfig(
                    name=name or 'UPS',
                    description=description,
                    poll_interval=poll_interval or 5,
                    nut_device_name=nut_device_name or 'ups',
                    nut_driver=nut_driver or 'usbhid-ups',
                    nut_port=nut_port,
                    nut_username=nut_username or 'admin',
                    nut_password=nut_password or '',
                    nut_retry_count=nut_retry_count or 3,
                    nut_retry_delay=nut_retry_delay or 5
                )
                session.add(ups_config)
                session.commit()
        finally:
            session.close()
    
    def update_health_check(self, enabled=None, notification_time=None):
        """Update health check settings."""
        session = self.get_session()
        try:
            health_check = session.query(HealthCheck).first()
            if health_check:
                if enabled is not None:
                    health_check.enabled = enabled
                if notification_time is not None:
                    health_check.notification_time = notification_time
                session.commit()
        finally:
            session.close()
    
    def update_battery_health_config(self, **kwargs):
        """Update battery health configuration."""
        session = self.get_session()
        try:
            config = session.query(BatteryHealthConfig).first()
            if config:
                for key, value in kwargs.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                session.commit()
            else:
                config = BatteryHealthConfig(**kwargs)
                session.add(config)
                session.commit()
        finally:
            session.close()
    
    def get_battery_health_history(self, limit=24):
        """Get recent battery health history records."""
        session = self.get_session()
        try:
            return session.query(BatteryHealthHistory)\
                .order_by(BatteryHealthHistory.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def get_recent_alerts(self, limit=10):
        """Get recent battery alerts."""
        session = self.get_session()
        try:
            return session.query(BatteryAlert)\
                .order_by(BatteryAlert.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def add_battery_health_history(self, **kwargs):
        """Add a new battery health history record."""
        session = self.get_session()
        try:
            history = BatteryHealthHistory(**kwargs)
            session.add(history)
            session.commit()
        finally:
            session.close()
    
    def add_battery_alert(self, alert_type, value, threshold):
        """Add a new battery alert."""
        session = self.get_session()
        try:
            alert = BatteryAlert(
                alert_type=alert_type,
                value=value,
                threshold=threshold
            )
            session.add(alert)
            session.commit()
        finally:
            session.close()
    
    def resolve_battery_alert(self, alert_id):
        """Resolve a battery alert."""
        session = self.get_session()
        try:
            alert = session.query(BatteryAlert).get(alert_id)
            if alert:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                session.commit()
        finally:
            session.close()
    
    def update_notification_service(self, service_type, enabled=None, **kwargs):
        """Update notification service settings."""
        session = self.get_session()
        try:
            service = session.query(NotificationService).filter_by(service_type=service_type).first()
            if not service:
                service = NotificationService(service_type=service_type)
                session.add(service)
            
            if enabled is not None:
                service.enabled = enabled
            
            if service_type == 'webhook':
                if 'webhook_config' in kwargs:
                    config = service.webhook_config or WebhookConfig()
                    for key, value in kwargs['webhook_config'].items():
                        if key == 'headers' and value:
                            try:
                                if isinstance(value, str):
                                    value = json.loads(value)
                                config.headers = json.dumps(value)
                            except json.JSONDecodeError:
                                raise ValueError("Invalid JSON format for headers")
                        else:
                            setattr(config, key, value)
                    service.webhook_config = config
            
            elif service_type == 'email':
                if 'email_config' in kwargs:
                    config = service.email_config or EmailConfig()
                    for key, value in kwargs['email_config'].items():
                        if key == 'smtp_password' and not value:
                            continue  # Skip empty password updates
                        setattr(config, key, value)
                    service.email_config = config
            
            elif service_type == 'sms':
                if 'sms_config' in kwargs:
                    config = service.sms_config or SMSConfig()
                    for key, value in kwargs['sms_config'].items():
                        if key == 'auth_token' and not value:
                            continue  # Skip empty token updates
                        setattr(config, key, value)
                    service.sms_config = config
            
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating notification service: {str(e)}")
            raise
        finally:
            session.close()
    
    def is_setup_completed(self):
        """Check if initial setup has been completed."""
        session = self.get_session()
        try:
            web_interface = session.query(WebInterface).first()
            return web_interface and web_interface.setup_completed
        finally:
            session.close()

    def get_webhook_config(self):
        """Get webhook notification configuration."""
        session = self.get_session()
        try:
            service = session.query(NotificationService).filter_by(service_type='webhook').first()
            return service.webhook_config if service else None
        finally:
            session.close()

    def get_email_config(self):
        """Get email notification configuration."""
        session = self.get_session()
        try:
            service = session.query(NotificationService).filter_by(service_type='email').first()
            return service.email_config if service else None
        finally:
            session.close()

    def get_sms_config(self):
        """Get SMS notification configuration."""
        session = self.get_session()
        try:
            service = session.query(NotificationService).filter_by(service_type='sms').first()
            return service.sms_config if service else None
        finally:
            session.close()

    def update_webhook_config(self, url, method='POST', timeout=30, headers=None):
        """Update webhook configuration."""
        session = self.get_session()
        try:
            service = session.query(NotificationService).filter_by(service_type='webhook').first()
            if not service:
                service = NotificationService(service_type='webhook')
                session.add(service)
            
            if not service.webhook_config:
                service.webhook_config = WebhookConfig()
            
            service.enabled = True
            service.webhook_config.url = url
            service.webhook_config.method = method
            service.webhook_config.timeout = timeout
            
            # Handle headers JSON serialization
            if headers is not None:
                if isinstance(headers, str):
                    try:
                        # If headers is a JSON string, parse it
                        headers = json.loads(headers)
                    except json.JSONDecodeError:
                        raise ValueError("Invalid JSON format for headers")
                service.webhook_config.headers = json.dumps(headers)
            else:
                service.webhook_config.headers = None
            
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating webhook config: {str(e)}")
            raise
        finally:
            session.close() 