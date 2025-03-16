#!/usr/bin/env python3
"""
Power Snitch Auth Blueprint
Handles single-user authentication routes and functionality.
"""

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from web.extensions import db
from app.web.forms.form_auth import LoginForm
from web.models.web_interface import WebInterface

# Configure logging
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle single-user login."""
    if current_user.is_authenticated:
        logger.info("User already authenticated, redirecting to dashboard")
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Get web interface settings which contains the password hash
            web_interface = WebInterface.get_config()
            if not web_interface:
                logger.error("Web interface settings not found")
                flash('System configuration error', 'error')
                return render_template('login.html', form=form)
            
            if web_interface.check_password(form.password.data):
                # Create a simple user object for Flask-Login
                user = type('User', (), {
                    'is_authenticated': True,
                    'is_active': True,
                    'is_anonymous': False,
                    'get_id': lambda self: '1'  # Single user always has ID 1
                })()
                
                login_user(user)
                logger.info("User logged in successfully")
                
                # Check if setup is complete
                if not web_interface.setup_completed:
                    logger.info("Setup not completed, redirecting to setup page")
                    return redirect(url_for('settings.setup'))
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.index'))
            
            logger.error("Failed login attempt")
            flash('Invalid password', 'error')
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    try:
        logout_user()
        logger.info("User logged out successfully")
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        flash('An error occurred during logout. Please try again.', 'error')
        return redirect(url_for('dashboard.index')) 