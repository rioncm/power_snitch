#!/usr/bin/env python3
"""
Power Snitch Trigger Model
Handles notification triggers and always notify events.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import relationship
from web.db import Base

class Trigger(Base):
    """Trigger model for notification events."""
    
    __tablename__ = 'triggers'
    
    id = Column(Integer, primary_key=True)
    trigger_type = Column(String, CheckConstraint("trigger_type IN ('battery_level_change', 'load_change', 'always_notify', 'health_check')"), nullable=False)
    value = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    always_notify_events = relationship("AlwaysNotifyEvent", back_populates="trigger")
    
    @classmethod
    def get_all(cls):
        """Get all triggers."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls).all()
        finally:
            session.close()
    
    def save(self):
        """Save trigger to database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()

class AlwaysNotifyEvent(Base):
    """Always notify event model."""
    
    __tablename__ = 'always_notify_events'
    
    id = Column(Integer, primary_key=True)
    trigger_id = Column(Integer, ForeignKey('triggers.id'), nullable=False)
    event_type = Column(String, CheckConstraint("event_type IN ('power_failure', 'power_restored', 'low_battery', 'health_check')"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    trigger = relationship("Trigger", back_populates="always_notify_events")
    
    @classmethod
    def get_all(cls):
        """Get all always notify events."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls).all()
        finally:
            session.close()
    
    def save(self):
        """Save event to database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close() 