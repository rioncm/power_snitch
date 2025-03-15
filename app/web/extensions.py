#!/usr/bin/env python3
"""
Power Snitch Extensions Module
Initializes and configures Flask extensions.
"""

from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from db import Database

# Initialize extensions
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Initialize database
db = Database('/opt/power_snitch/data/power_snitch.db')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Since we have a single user system, we just need to verify the ID is '1'
    if user_id == '1':
        # Create a simple user object that Flask-Login expects
        return type('User', (), {
            'is_authenticated': True,
            'is_active': True,
            'is_anonymous': False,
            'get_id': lambda: '1'
        })()
    return None

def init_extensions(app):
    """Initialize all Flask extensions."""
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Initialize login manager
    login_manager.init_app(app)
    
    # Register database with app
    app.db = db 