#!/usr/bin/env python3
"""
Power Snitch Auth Blueprint
Handles single-user authentication routes and functionality.
"""

import logging

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from web.extensions import db
from web.forms.form_auth import LoginForm
from web.models.web_interface import WebInterface

# Configure logging
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login():
    with db.session_scope() as session:
        web_interface = WebInterface.get_config(session)
    
        if request.method == 'GET':
            if current_user.is_authenticated:
                if not web_interface or not web_interface.setup_completed:
                    logger.info("Setup not completed, redirecting to setup page")
                    return redirect(url_for('setup.index'))
                logger.info("User already authenticated, redirecting to dashboard")
                return redirect(url_for('dashboard.index'))
            
            logger.info("User not authenticated, showing login page")
            return render_template('login.html', form=LoginForm())
    
    
@auth_bp.route('/authorize', methods=['POST'])
def authorize():
    """API endpoint for user login."""
    
    form = LoginForm(request.form)  # Ensure form is populated

    # Validate form before accessing its fields
    if not form.validate_on_submit():
        return jsonify({'error': 'Invalid input. Please try again.'}), 400
    
    try:
        with db.session_scope() as session:
            web_interface = WebInterface.get_config(session)
            if not web_interface:
                return jsonify({'error': 'Web interface settings not found'}), 500
            
            # Check if password is correct
            if web_interface.check_password(form.password.data):
                # Temporary user object (Sufficient for Power Snitch's single-user model)
                user = type('User', (), {
                    'is_authenticated': True,
                    'is_active': True,
                    'is_anonymous': False,
                    'get_id': lambda self: '1'
                })()
                
                login_user(user)
                logger.info("API user logged in successfully")

                # Correct redirect logic based on setup completion
                redirect_url = url_for('dashboard.index') if web_interface.setup_completed else url_for('setup.index')
                return jsonify({'redirect_url': redirect_url}), 200
                #return jsonify({"message": f"Login Successful, setup status {web_interface.setup_completed} sending to {redirect_url}"}), 200
            
            logger.warning("Failed API login attempt")
            return jsonify({'error': 'Your password is invalid, please try again'}), 401

    except Exception as e:
        logger.error(f"Error during API login: {str(e)}")
        return jsonify({'error': 'An error occurred during login. Please try again.'})


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