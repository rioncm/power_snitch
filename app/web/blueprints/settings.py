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
from app.web.forms.form_settings import (
    SetupUPSSettingsForm,
    WebhookSettingsForm,
    EmailSettingsForm,
    SMSSettingsForm,
    WebInterfaceSettingsForm
)

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    """Display the settings page."""
    ups_settings = UPS.get_settings()
    webhook_config = NotificationService.get_webhook_config()
    email_config = NotificationService.get_email_config()
    sms_config = NotificationService.get_sms_config()
    system_settings = SystemSettings.get_settings()
    
    return render_template('settings/index.html',
                         ups_settings=ups_settings,
                         webhook_config=webhook_config,
                         email_config=email_config,
                         sms_config=sms_config,
                         system_settings=system_settings)

@settings_bp.route('/setup', methods=['GET'])
def setup():
    """Initial setup page for Power Snitch."""
    try:
        with db.session_scope() as session:
            web_interface_form = WebInterfaceSettingsForm()
            ups_form = SetupUPSSettingsForm()
            
            # Get web interface config
            web_interface_config = WebInterface.get_config(session)
            
            # Get UPS info if available
            ups = UPS.get_config(session)
            
            return render_template('setup.html',
                                web_interface_form=web_interface_form,
                                ups_form=ups_form,
                                ups=ups,
                                config={'web_interface': web_interface_config})
    except Exception as e:
        flash(f'Error loading setup page: {str(e)}', 'error')
        return render_template('setup.html',
                            web_interface_form=WebInterfaceSettingsForm(),
                            ups_form=SetupUPSSettingsForm())

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

@settings_bp.route('/webhook', methods=['POST'])
@login_required
def update_webhook_settings():
    """Update webhook settings."""
    form = WebhookSettingsForm()
    if form.validate_on_submit():
        config = NotificationService.get_webhook_config()
        config.update(form.data)
        config.save()
        return jsonify({'success': True, 'message': 'Webhook settings updated successfully'})
    return jsonify({'success': False, 'errors': form.errors}), 400

@settings_bp.route('/email', methods=['POST'])
@login_required
def update_email_settings():
    """Update email settings."""
    form = EmailSettingsForm()
    if form.validate_on_submit():
        config = NotificationService.get_email_config()
        config.update(form.data)
        config.save()
        return jsonify({'success': True, 'message': 'Email settings updated successfully'})
    return jsonify({'success': False, 'errors': form.errors}), 400

@settings_bp.route('/sms', methods=['POST'])
@login_required
def update_sms_settings():
    """Update SMS settings."""
    form = SMSSettingsForm()
    if form.validate_on_submit():
        config = NotificationService.get_sms_config()
        config.update(form.data)
        config.save()
        return jsonify({'success': True, 'message': 'SMS settings updated successfully'})
    return jsonify({'success': False, 'errors': form.errors}), 400

@settings_bp.route('/system', methods=['POST'])
@login_required
def update_system_settings():
    """Update system settings."""
    data = request.get_json()
    settings = SystemSettings.get_settings()
    settings.update(data)
    settings.save()
    return jsonify({'success': True, 'message': 'System settings updated successfully'}) 