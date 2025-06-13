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
# Configure logging
import logging
logger = logging.getLogger(__name__)

class WebInterface(Base):
    """Model for web interface configuration."""
    
    __tablename__ = 'web_interface'
    
    id = Column(Integer, primary_key=True)
    port = Column(Integer, CheckConstraint('port >= 1 AND port <= 65535'), nullable=False, default=80)
    password_hash = Column(String, nullable=False)
    setup_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    
     
    @staticmethod
    def set_password(new_password):
        with db.session_scope() as session:
            config = session.query(WebInterface).first()
            if config:
                config.password_hash = generate_password_hash(new_password)
                logger.info("Password updated successfully.")
                session.commit()
            else:
                logger.error("Password was not updated, config not found.")
                raise RuntimeError("WebInterface row not found.")
    
    def check_password(self, password):
        """Check the password against the stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def check_default_password(cls, password, session):
        """Check the password against the stored hash."""
        config = session.query(cls).first()
        logger.debug(f"Testing {generate_password_hash(password)} against the database {config.password_hash}")
        return check_password_hash(config.password_hash, password)
    
    @classmethod
    def get_config(cls, session):
        """Get the web interface configuration."""
        try:
            return session.query(cls).first()
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve web interface configuration: {str(e)}")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'port': self.port,
            'setup_completed': self.setup_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 