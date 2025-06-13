#!/usr/bin/env python3
"""
Power Snitch Notification Service Model
Handles notification service configurations and operations.
"""

import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, CheckConstraint, ForeignKey, func
from sqlalchemy.orm import relationship
from web.db import Base

class NotificationService(Base):
    """Base class for notification services."""
    
    __tablename__ = 'notification_services'
    
    id = Column(Integer, primary_key=True)
    service_type = Column(String(20), CheckConstraint("service_type IN ('webhook', 'email', 'sms')"), nullable=False, unique=True)
    enabled = Column(Boolean, default=False)
    last_test = Column(String)
    last_test_status = Column(Boolean)
    last_test_message = Column(Text)
    created_at = Column(String, nullable=False, default=func.current_timestamp())
    updated_at = Column(String, nullable=False, default=func.current_timestamp())
    
    __mapper_args__ = {
        'polymorphic_identity': 'notification_service',
        'polymorphic_on': service_type
    }
    
    def save(self):
        """Save notification service to database."""
        from web.extensions import db
        with db.session_scope() as session:
            session.add(self)
    
    def test(self):
        """Test the notification service."""
        try:
            success = self._send_test_notification()
            self.last_test = datetime.utcnow().isoformat()
            self.last_test_status = success
            self.last_test_message = "Test successful" if success else "Test failed"
            self.save()
            return success
        except Exception as e:
            self.last_test = datetime.utcnow().isoformat()
            self.last_test_status = False
            self.last_test_message = str(e)
            self.save()
            return False
    
    def _send_test_notification(self):
        """Send a test notification. Must be implemented by subclasses."""
        raise NotImplementedError

    @classmethod
    def get_webhook_config(cls):
        """Get webhook configuration."""
        return WebhookConfig.get_config()
    
    @classmethod
    def get_email_config(cls):
        """Get email configuration."""
        return EmailConfig.get_config()
    
    @classmethod
    def get_sms_config(cls):
        """Get SMS configuration."""
        return SMSConfig.get_config()

class WebhookConfig(Base):
    """Webhook configuration."""
    
    __tablename__ = 'webhook_config'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('notification_services.id'), nullable=False)
    url = Column(String(255), nullable=False)
    method = Column(String(10), CheckConstraint("method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')"), default='POST')
    timeout = Column(Integer, default=10)
    headers = Column(Text)
    created_at = Column(String, nullable=False, default=func.current_timestamp())
    updated_at = Column(String, nullable=False, default=func.current_timestamp())
    
    # Relationship
    service = relationship("NotificationService", backref="webhook_config")
    
    @classmethod
    def get_config(cls):
        """Get webhook configuration."""
        from web.extensions import db
        with db.session_scope() as session:
            service = session.query(NotificationService).filter_by(service_type='webhook').first()
            if not service:
                service = NotificationService(service_type='webhook')
                session.add(service)
                session.flush()
            
            config = session.query(cls).filter_by(service_id=service.id).first()
            if not config:
                config = cls(service_id=service.id)
                session.add(config)
            
            return config

class EmailConfig(Base):
    """Email configuration."""
    
    __tablename__ = 'email_config'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('notification_services.id'), nullable=False)
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_username = Column(String(255), nullable=False)
    smtp_password = Column(String(255), nullable=False)
    use_tls = Column(Boolean, default=True)
    created_at = Column(String, nullable=False, default=func.current_timestamp())
    updated_at = Column(String, nullable=False, default=func.current_timestamp())
    
    # Relationship
    service = relationship("NotificationService", backref="email_config")
    recipients = relationship("EmailRecipient", backref="config", cascade="all, delete-orphan")
    
    @classmethod
    def get_config(cls):
        """Get email configuration."""
        from web.extensions import db
        with db.session_scope() as session:
            service = session.query(NotificationService).filter_by(service_type='email').first()
            if not service:
                service = NotificationService(service_type='email')
                session.add(service)
                session.flush()
            
            config = session.query(cls).filter_by(service_id=service.id).first()
            if not config:
                config = cls(service_id=service.id)
                session.add(config)
            
            return config

class EmailRecipient(Base):
    """Email recipient model."""
    
    __tablename__ = 'email_recipients'
    
    id = Column(Integer, primary_key=True)
    email_config_id = Column(Integer, ForeignKey('email_config.id'), nullable=False)
    email_address = Column(String(255), nullable=False)
    created_at = Column(String, nullable=False, default=func.current_timestamp())

class SMSConfig(Base):
    """SMS configuration."""
    
    __tablename__ = 'sms_config'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('notification_services.id'), nullable=False)
    twilio_account_sid = Column(String(255), nullable=False)
    twilio_auth_token = Column(String(255), nullable=False)
    twilio_from_number = Column(String(20), nullable=False)
    created_at = Column(String, nullable=False, default=func.current_timestamp())
    updated_at = Column(String, nullable=False, default=func.current_timestamp())
    
    # Relationship
    service = relationship("NotificationService", backref="sms_config")
    recipients = relationship("SMSRecipient", backref="config", cascade="all, delete-orphan")
    
    @classmethod
    def get_config(cls):
        """Get SMS configuration."""
        from web.extensions import db
        with db.session_scope() as session:
            service = session.query(NotificationService).filter_by(service_type='sms').first()
            if not service:
                service = NotificationService(service_type='sms')
                session.add(service)
                session.flush()
            
            config = session.query(cls).filter_by(service_id=service.id).first()
            if not config:
                config = cls(service_id=service.id)
                session.add(config)
            
            return config

class SMSRecipient(Base):
    """SMS recipient model."""
    
    __tablename__ = 'sms_recipients'
    
    id = Column(Integer, primary_key=True)
    sms_config_id = Column(Integer, ForeignKey('sms_config.id'), nullable=False)
    phone_number = Column(String(20), nullable=False)
    created_at = Column(String, nullable=False, default=func.current_timestamp()) 