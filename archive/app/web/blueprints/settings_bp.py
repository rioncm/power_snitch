#!/usr/bin/env python3
"""
Power Snitch Settings Blueprint
Handles configuration and settings management.
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
    ChangePassword,
    WebhookSettingsForm,
    EmailSettingsForm,
    SMSSettingsForm,
    WebInterfaceSettingsForm
)
# Configure logging
import logging
logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    """Display the edit settings page."""
    ups_settings = UPS.get_config()
    webhook_config = NotificationService.get_webhook_config()
    email_config = NotificationService.get_email_config()
    sms_config = NotificationService.get_sms_config()
    system_settings = SystemSettings.get_settings()
    
    return render_template('settings.html',
                         ups_settings=ups_settings,
                         webhook_config=webhook_config,
                         email_config=email_config,
                         sms_config=sms_config,
                         system_settings=system_settings)


@settings_bp.route('/password', methods=['POST'])
@login_required
def change_password():
    """Update web interface settings."""
    form = ChangePassword()
    
    if not form.validate_on_submit():
        return jsonify({
            'success': False,
            'errors': form.errors
        }), 400
    
    try:
        WebInterface.set_password(form.password.data)
        logger.info("Password Updated")
            
        return jsonify({
            'success': True,
            'message': 'Web interface settings updated successfully'
        }),200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update password: {str(e)}'
        }), 500

@settings_bp.route('/ups/description', methods=['POST'])
def ups_description():
    """Update UPS settings."""
    form = SetupUPS()
    logger.debug("Updating UPS Description")
    if not form.validate_on_submit():
        logger.error("UPS Description form validation failed")
        return jsonify({
            'success': False,
            'errors': form.errors
        }), 400
    logger.debug("UPS Description form validated")
    try:
        with db.session_scope() as session:
            ups = UPS.get_config(session)
            if not ups:
                return jsonify({
                    'success': False,
                    'error': 'No UPS configuration found'
                }), 404
            logger.debug("UPS Configuration found")
            logger.debug(f"Updating UPS Description to {form.description.data} from {ups.description}")
            ups.description = form.description.data
            logger.debug(f"UPS Description updated to {ups.description}")
            session.commit()
            logger.info("UPS description updated")
            return jsonify({
                'success': True,
                'message': 'UPS description updated successfully'
            })
    except Exception as e:
        logger.error(f"UPS Description update failed with {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to update UPS settings: {str(e)}'
        }), 500

