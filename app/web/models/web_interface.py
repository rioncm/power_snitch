#!/usr/bin/env python3
"""
Power Snitch Web Interface Model
Handles web interface configuration.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from web.db import Base
from web.extensions import db

class WebInterface(Base):
    """Model for web interface configuration."""
    
    __tablename__ = 'web_interface'
    
    id = Column(Integer, primary_key=True)
    port = Column(Integer, nullable=False, default=80)
    password_hash = Column(String, nullable=False)
    setup_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_config(cls):
        """Get the web interface configuration."""
        session = db.get_session()  # Get a session that will be kept alive
        try:
            config = session.query(cls).first()
            if not config:
                config = cls()
                session.add(config)
                session.commit()
                config = session.query(cls).first()  # Refresh the instance
            return config
        except Exception as e:
            session.rollback()
            raise
    
    def save(self):
        """Save the configuration."""
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'port': self.port,
            'setup_completed': self.setup_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 