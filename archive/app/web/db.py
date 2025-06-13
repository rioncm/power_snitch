#!/usr/bin/env python3
"""
Power Snitch Database Module
Handles core database operations using SQLAlchemy.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

logger = logging.getLogger(__name__)
Base = declarative_base()

class Database:
    """Core database functionality."""
    
    def __init__(self, db_path):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    @contextmanager
    def session_scope(self):
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
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    # Properties    
    @property
    def path(self):
        """Return the current database path as a string."""
        return str(self.engine.url)
    
 