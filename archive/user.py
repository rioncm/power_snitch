#!/usr/bin/env python3
"""
Power Snitch User Model
Handles user authentication and database operations.
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Boolean
from web.db import Base

class User(UserMixin, Base):
    """User model for authentication and authorization."""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    def __init__(self, username, email):
        """Initialize a new user."""
        self.username = username
        self.email = email
    
    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)
    
    def save(self):
        """Save the user to the database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by ID."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls).get(user_id)
        finally:
            session.close()
    
    @classmethod
    def get_by_username(cls, username):
        """Get a user by username."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls).filter_by(username=username).first()
        finally:
            session.close()
    
    @classmethod
    def get_by_email(cls, email):
        """Get a user by email."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls).filter_by(email=email).first()
        finally:
            session.close()
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin
        } 