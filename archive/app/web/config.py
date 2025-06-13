#!/usr/bin/env python3
"""
Power Snitch Configuration Module
Handles all configuration settings for the web application.
"""

import os
import logging
from pathlib import Path

# Development key - this will be replaced by install process later
DEV_SECRET_KEY = 'dev-power-snitch-key-2024'

class Config:
    """Base configuration class."""
    
    # Base paths
    BASE_DIR = Path('/opt/power_snitch')
    DATA_DIR = BASE_DIR / 'data'
    LOG_DIR = BASE_DIR / 'logs'
    
    # Database
    DATABASE_PATH = DATA_DIR / 'power_snitch.db'
    
    # Logging
    LOG_FILE = LOG_DIR / 'web_app.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = logging.DEBUG
    
    # Flask and Security
    SECRET_KEY = DEV_SECRET_KEY
    WTF_CSRF_SECRET_KEY = DEV_SECRET_KEY
    WTF_CSRF_ENABLED = True
    
    # Session - HTTP only cookie flag for basic security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # HTTP-only application
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration."""
        # Ensure directories exist
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=cls.LOG_LEVEL,
            format=cls.LOG_FORMAT,
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        # Configure Flask
        app.config.from_object(cls)
        
        # Additional Flask configurations
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session lifetime

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = ':memory:'  # Use in-memory SQLite for testing

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # In production, these should be set from environment variables or generated during install
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', DEV_SECRET_KEY)
    WTF_CSRF_SECRET_KEY = os.environ.get('FLASK_CSRF_SECRET_KEY', DEV_SECRET_KEY)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 