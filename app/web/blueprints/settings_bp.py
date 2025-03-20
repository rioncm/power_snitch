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
    UPSSettingsForm,
    WebhookSettingsForm,
    EmailSettingsForm,
    SMSSettingsForm,
    WebInterfaceSettingsForm
)

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    """Display the edit settings page."""
    ups_settings = UPS.get_ups_config()
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


@settings_bp.route('/web-interface/update', methods=['POST'])
def update_web_interface_settings():
    """Update web interface settings."""
    form = WebInterfaceSettingsForm()
    
    if not form.validate_on_submit():
        return jsonify({
            'success': False,
            'errors': form.errors
        }), 400
    
    try:
        with db.session_scope() as session:
            config = WebInterface.get_config(session)
            if not config:
                config = WebInterface()
                session.add(config)
            
            config.password = form.password.data
            config.setup_completed = True
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Web interface settings updated successfully'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update settings: {str(e)}'
        }), 500

@settings_bp.route('/ups/update', methods=['POST'])
def update_ups_settings():
    """Update UPS settings."""
    form = UPSSettingsForm()
    
    if not form.validate_on_submit():
        return jsonify({
            'success': False,
            'errors': form.errors
        }), 400
    
    try:
        with db.session_scope() as session:
            ups = UPS.get_config(session)
            if not ups:
                return jsonify({
                    'success': False,
                    'error': 'No UPS configuration found'
                }), 404
            
            ups.description = form.description.data
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'UPS description updated successfully'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update UPS settings: {str(e)}'
        }), 500

