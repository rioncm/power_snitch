#!/usr/bin/env python3
"""
Power Snitch Health Check Model
Handles health check settings and operations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, Time, func
from web.db import Base

class HealthCheck(Base):
    """Health check settings model."""
    
    __tablename__ = 'health_check'
    
    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, nullable=False, default=False)
    notification_time = Column(Time, nullable=False)
    last_notification = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_settings(cls):
        """Get health check settings."""
        from web.extensions import db
        session = db.get_session()
        try:
            settings = session.query(cls).first()
            if not settings:
                settings = cls()
                session.add(settings)
                session.commit()
            return settings
        finally:
            session.close()
    
    def save(self):
        """Save health check settings."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    def update(self, enabled=None, notification_time=None):
        """Update health check settings."""
        if enabled is not None:
            self.enabled = enabled
        if notification_time is not None:
            self.notification_time = notification_time
        self.save()
    
    def record_notification(self):
        """Record that a health check notification was sent."""
        self.last_notification = datetime.utcnow()
        self.save() 