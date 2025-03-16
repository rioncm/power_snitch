#!/usr/bin/env python3
"""
Power Snitch Web Interface Model
Handles web interface configuration.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from web.db import Base
from web.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class WebInterface(Base):
    """Model for web interface configuration."""
    
    __tablename__ = 'web_interface'
    
    id = Column(Integer, primary_key=True)
    port = Column(Integer, CheckConstraint('port >= 1 AND port <= 65535'), nullable=False, default=80)
    password_hash = Column(String, nullable=False)
    setup_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set the password hash."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check the password against the stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    

    @classmethod
    def get_config(cls, session=None):
        """Get the web interface configuration."""
        from web.extensions import db
    
        if session is None:
            session = db.get_session()  # Use get_session to get a session instance
    
        config = session.query(cls).first()
        if not config:
            config = cls()
            session.add(config)
            session.commit()  # Commit changes to persist the new config
            session.refresh(config)  # Refresh to ensure all attributes are loaded
        return config
    
    def save(self):
        """Save the configuration."""
        from web.extensions import db
    
        session = db.get_session()  # Use get_session to get a session instance
        try:
            if not self.password_hash:
                raise ValueError("Password hash must be set before saving")
            self.updated_at = datetime.utcnow()
            session.add(self)
            session.commit()  # Commit changes to persist the object
        except Exception:
            session.rollback()  # Rollback in case of an error
            raise
        finally:
            session.close()  # Ensure the session is closed
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'port': self.port,
            'setup_completed': self.setup_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 