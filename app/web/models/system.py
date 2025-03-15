#!/usr/bin/env python3
"""
Power Snitch System Settings Model
Handles application-wide settings and configuration.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from web.db import Base

class SystemSettings(Base):
    """System settings model for application-wide configuration."""
    
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    setup_completed = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)
    debug_mode = Column(Boolean, default=False)
    log_level = Column(String(20), default='INFO')
    api_key = Column(String(64), unique=True)
    last_backup = Column(DateTime)
    backup_frequency = Column(Integer, default=24)  # hours
    retention_period = Column(Integer, default=30)  # days
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self):
        """Initialize system settings with default values."""
        self.setup_completed = False
        self.maintenance_mode = False
        self.debug_mode = False
        self.log_level = 'INFO'
        self.backup_frequency = 24
        self.retention_period = 30
    
    def save(self):
        """Save system settings to database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    def update(self, data):
        """Update system settings with new data."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
    
    @classmethod
    def get_settings(cls):
        """Get system settings."""
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
    
    def to_dict(self):
        """Convert system settings to dictionary."""
        return {
            'id': self.id,
            'setup_completed': self.setup_completed,
            'maintenance_mode': self.maintenance_mode,
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'last_backup': self.last_backup.isoformat() if self.last_backup else None,
            'backup_frequency': self.backup_frequency,
            'retention_period': self.retention_period,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 