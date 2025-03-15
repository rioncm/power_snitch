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
    service_type = Column(String(20), CheckConstraint("service_type IN ('webhook', 'email', 'sms')"), nullable=False)
    enabled = Column(Boolean, default=False)
    last_test = Column(String)  # TEXT in SQLite
    last_test_status = Column(Boolean)
    last_test_message = Column(Text)
    created_at = Column(String, nullable=False, default=func.current_timestamp())  # TEXT in SQLite
    updated_at = Column(String, nullable=False, default=func.current_timestamp())  # TEXT in SQLite
    
    __mapper_args__ = {
        'polymorphic_identity': 'notification_service',
        'polymorphic_on': service_type
    }
    
    def save(self):
        """Save notification service to database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
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

class WebhookService(NotificationService):
    """Webhook notification service."""
    
    __tablename__ = 'webhook_config'
    
    id = Column(Integer, ForeignKey('notification_services.id', ondelete='CASCADE'), primary_key=True)
    url = Column(String(255), nullable=False)
    method = Column(String(10), CheckConstraint("method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')"), default='POST')
    timeout = Column(Integer, default=10)
    headers = Column(Text)
    
    __mapper_args__ = {
        'polymorphic_identity': 'webhook'
    }
    
    def __init__(self):
        """Initialize webhook service."""
        super().__init__()
        self.service_type = 'webhook'
    
    def _send_test_notification(self):
        """Send a test webhook notification."""
        if not self.enabled or not self.url:
            return False
        
        headers = {}
        if self.headers:
            try:
                headers = json.loads(self.headers)
            except json.JSONDecodeError:
                return False
        
        data = {
            'type': 'test',
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Test notification from Power Snitch'
        }
        
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            return response.status_code in (200, 201, 202)
        except Exception:
            return False
    
    def send_notification(self, data):
        """Send a webhook notification."""
        if not self.enabled or not self.url:
            return False
        
        headers = {}
        if self.headers:
            try:
                headers = json.loads(self.headers)
            except json.JSONDecodeError:
                return False
        
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            return response.status_code in (200, 201, 202)
        except Exception:
            return False

class EmailService(NotificationService):
    """Email notification service."""
    
    __tablename__ = 'email_config'
    
    id = Column(Integer, ForeignKey('notification_services.id', ondelete='CASCADE'), primary_key=True)
    smtp_server = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    from_email = Column(String(255), nullable=False)
    to_email = Column(String(255), nullable=False)
    use_tls = Column(Boolean, default=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'email'
    }
    
    def __init__(self):
        """Initialize email service."""
        super().__init__()
        self.service_type = 'email'
    
    def _send_test_notification(self):
        """Send a test email notification."""
        if not self.enabled or not all([self.smtp_server, self.smtp_port, self.username, self.from_email, self.to_email]):
            return False
        
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = 'Power Snitch Test Notification'
        
        body = 'This is a test notification from Power Snitch.'
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception:
            return False
    
    def send_notification(self, subject, body):
        """Send an email notification."""
        if not self.enabled or not all([self.smtp_server, self.smtp_port, self.username, self.from_email, self.to_email]):
            return False
        
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception:
            return False

class SMSService(NotificationService):
    """SMS notification service."""
    
    __tablename__ = 'sms_config'
    
    id = Column(Integer, ForeignKey('notification_services.id', ondelete='CASCADE'), primary_key=True)
    provider = Column(String(50), CheckConstraint("provider IN ('twilio')"), nullable=False)
    account_sid = Column(String(255), nullable=False)
    auth_token = Column(String(255), nullable=False)
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'sms'
    }
    
    def __init__(self):
        """Initialize SMS service."""
        super().__init__()
        self.service_type = 'sms'
    
    def _send_test_notification(self):
        """Send a test SMS notification."""
        if not self.enabled or not all([self.provider, self.account_sid, self.auth_token, self.from_number, self.to_number]):
            return False
        
        try:
            if self.provider == 'twilio':
                from twilio.rest import Client
                client = Client(self.account_sid, self.auth_token)
                message = client.messages.create(
                    body='Test notification from Power Snitch',
                    from_=self.from_number,
                    to=self.to_number
                )
                return bool(message.sid)
            return False
        except Exception:
            return False
    
    def send_notification(self, message):
        """Send an SMS notification."""
        if not self.enabled or not all([self.provider, self.account_sid, self.auth_token, self.from_number, self.to_number]):
            return False
        
        try:
            if self.provider == 'twilio':
                from twilio.rest import Client
                client = Client(self.account_sid, self.auth_token)
                message = client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=self.to_number
                )
                return bool(message.sid)
            return False
        except Exception:
            return False

def get_webhook_config():
    """Get webhook configuration."""
    from web.extensions import db
    config = db.get_first_model(WebhookService)
    if not config:
        config = WebhookService()
        db.save_model(config)
    return config

def get_email_config():
    """Get email configuration."""
    from web.extensions import db
    config = db.get_first_model(EmailService)
    if not config:
        config = EmailService()
        db.save_model(config)
    return config

def get_sms_config():
    """Get SMS configuration."""
    from web.extensions import db
    config = db.get_first_model(SMSService)
    if not config:
        config = SMSService()
        db.save_model(config)
    return config 