#!/usr/bin/env python3
"""
Power Snitch Database Module
Handles core database operations using SQLAlchemy.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Create base class for declarative models
Base = declarative_base()

class Database:
    """Core database functionality."""
    
    def __init__(self, db_path):
        """Initialize database connection."""
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def init_db(self):
        """Initialize database tables."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def get_model_by_id(self, model_class, model_id):
        """Generic method to get a model instance by ID."""
        with self.session_scope() as session:
            return session.query(model_class).get(model_id)
    
    def get_first_model(self, model_class):
        """Generic method to get the first instance of a model."""
        with self.session_scope() as session:
            return session.query(model_class).first()
    
    def save_model(self, model_instance):
        """Generic method to save a model instance."""
        with self.session_scope() as session:
            session.add(model_instance)
            session.commit()
            return model_instance
    
    def delete_model(self, model_instance):
        """Generic method to delete a model instance."""
        with self.session_scope() as session:
            session.delete(model_instance)
            session.commit()
    
    def query_model(self, model_class):
        """Generic method to query a model."""
        with self.session_scope() as session:
            return session.query(model_class)
            
    def get_notification_service(self, service_type):
        """Get notification service by type."""
        from web.models.notification import NotificationService
        with self.session_scope() as session:
            return session.query(NotificationService).filter(
                NotificationService.service_type == service_type
            ).first() 