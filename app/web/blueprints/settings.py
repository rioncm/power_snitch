#!/usr/bin/env python3
"""
Power Snitch Settings Blueprint
Handles configuration and settings management.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from web.models.ups import UPS
from web.models.notification import NotificationService
from web.models.system import SystemSettings
from web.forms.settings import (
    UPSSettingsForm,
    WebhookSettingsForm,
    EmailSettingsForm,
    SMSSettingsForm
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

@settings_bp.route('/ups', methods=['POST'])
@login_required
def update_ups_settings():
    """Update UPS settings."""
    form = UPSSettingsForm()
    if form.validate_on_submit():
        settings = UPS.get_settings()
        settings.update(form.data)
        settings.save()
        return jsonify({'success': True, 'message': 'UPS settings updated successfully'})
    return jsonify({'success': False, 'errors': form.errors}), 400

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