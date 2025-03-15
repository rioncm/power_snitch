#!/usr/bin/env python3
"""
Power Snitch Alert Model
Handles system alerts and notifications.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, CheckConstraint, func
from web.db import Base

class Alert(Base):
    """Alert model for system notifications."""
    
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20), CheckConstraint("level IN ('info', 'warning', 'critical')"), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(80), CheckConstraint("source IN ('ups', 'system', 'notification')"), nullable=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __init__(self, level, message, source):
        """Initialize a new alert."""
        self.level = level
        self.message = message
        self.source = source
    
    def acknowledge(self):
        """Acknowledge the alert."""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.save()
    
    def save(self):
        """Save alert to database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    @classmethod
    def get_recent_alerts(cls, limit=10):
        """Get recent alerts."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls)\
                .order_by(cls.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    @classmethod
    def get_unacknowledged_alerts(cls):
        """Get unacknowledged alerts."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls)\
                .filter_by(acknowledged=False)\
                .order_by(cls.timestamp.desc())\
                .all()
        finally:
            session.close()
    
    @classmethod
    def create_ups_alert(cls, level, message):
        """Create a UPS-related alert."""
        alert = cls(level=level, message=message, source='ups')
        alert.save()
        return alert
    
    @classmethod
    def create_system_alert(cls, level, message):
        """Create a system-related alert."""
        alert = cls(level=level, message=message, source='system')
        alert.save()
        return alert
    
    @classmethod
    def create_notification_alert(cls, level, message):
        """Create a notification-related alert."""
        alert = cls(level=level, message=message, source='notification')
        alert.save()
        return alert
    
    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'source': self.source,
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 