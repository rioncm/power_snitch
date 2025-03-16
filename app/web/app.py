#!/usr/bin/env python3
"""
Power Snitch Web Application
Main application factory and entry point.
"""

import os
import logging
from flask import Flask, render_template
from config import config
from extensions import init_extensions
from web.models.web_interface import WebInterface

# Configure logging
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__,
                template_folder='templates',  # Templates will be in web/templates
                static_folder='static')       # Static files will be in web/static
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.settings import settings_bp
    from blueprints.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    return app

def start_web_interface():
    """Start the web interface."""
    try:
        app = create_app('production')  # Use production config by default
        
        # Get web interface config within app context
        with app.app_context():
            from web.models.web_interface import WebInterface
            from web.extensions import db
            
            with db.session_scope() as session:
                web_interface = WebInterface.get_config(session=session)
                port = web_interface.port  # Get port while in session
                
                if not web_interface.setup_completed:
                    logger.warning("Web interface not configured. Using default port 80.")
                    port = 80
        
        app.run(
            host='0.0.0.0',  # Always bind to all interfaces
            port=port,
            debug=True  # Production setting as per development rules
        )
    except Exception as e:
        logger.error(f"Failed to start web interface: {str(e)}")
        raise

if __name__ == '__main__':
    start_web_interface() 