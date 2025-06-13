#!/usr/bin/env python3
"""
Power Snitch setup Blueprint
Handles configuration and settings management for inital setup.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required
from web.models.ups import UPS
from web.models.notification import NotificationService
from web.models.system import SystemSettings
from web.models.web_interface import WebInterface
from web.models.notification import WebhookConfig, EmailConfig, SMSConfig
from web.extensions import db
from web.forms.form_settings import (
    SetupUPS,
    ChangePassword
)
setup_bp = Blueprint('setup', __name__)
# Configure logging
import logging
logger = logging.getLogger(__name__)

@setup_bp.route('/')
@login_required
def index():
    """Initial setup page for Power Snitch."""
    try:
        with db.session_scope() as session:
            web_interface_form = ChangePassword()
            ups_form = SetupUPS()
            
            # Get web interface config
            web_interface_config = WebInterface.get_config(session)
            default_password = WebInterface.check_default_password('password', session)
            # Get UPS info if available
            ups = UPS.get_config(session)
            logger.info("Rendering setup screen")
            return render_template('setup.html',
                                web_interface_form=web_interface_form,
                                ups_form=ups_form,
                                ups=ups,
                                config={'web_interface': web_interface_config},
                                default_password=default_password)
    except Exception as e:
        flash(f'Error loading setup page: {str(e)}', 'error')
        return render_template('setup.html',
                            web_interface_form=ChangePassword(),
                            ups_form=SetupUPS())

