#!/usr/bin/env python3
"""
Power Snitch API Blueprint
Handles API endpoints for external integrations.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from web.models.ups import UPS
from web.models.alert import Alert
from web.models.system import SystemSettings

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def get_status():
    """Get current UPS status."""
    ups = UPS.get_current_status()
    return jsonify(ups.to_dict())

@api_bp.route('/alerts')
def get_alerts():
    """Get recent alerts."""
    limit = request.args.get('limit', default=10, type=int)
    alerts = Alert.get_recent_alerts(limit=limit)
    return jsonify([alert.to_dict() for alert in alerts])

@api_bp.route('/battery-history')
def get_battery_history():
    """Get battery history."""
    limit = request.args.get('limit', default=24, type=int)
    ups = UPS.get_current_status()
    history = ups.get_battery_history(limit=limit)
    return jsonify([entry.to_dict() for entry in history])

@api_bp.route('/system/info')
def get_system_info():
    """Get system information."""
    settings = SystemSettings.get_settings()
    return jsonify(settings.to_dict())

@api_bp.route('/webhook/test', methods=['POST'])
@login_required
def test_webhook():
    """Test webhook configuration."""
    try:
        config = NotificationService.get_webhook_config()
        if not config.enabled:
            return jsonify({
                'success': False,
                'message': 'Webhook notifications are disabled'
            }), 400
        
        # Send test notification
        success = config.send_test_notification()
        if success:
            return jsonify({
                'success': True,
                'message': 'Test webhook notification sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test webhook notification'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing webhook: {str(e)}'
        }), 500

@api_bp.route('/email/test', methods=['POST'])
@login_required
def test_email():
    """Test email configuration."""
    try:
        config = NotificationService.get_email_config()
        if not config.enabled:
            return jsonify({
                'success': False,
                'message': 'Email notifications are disabled'
            }), 400
        
        # Send test email
        success = config.send_test_email()
        if success:
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test email'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing email: {str(e)}'
        }), 500

@api_bp.route('/sms/test', methods=['POST'])
@login_required
def test_sms():
    """Test SMS configuration."""
    try:
        config = NotificationService.get_sms_config()
        if not config.enabled:
            return jsonify({
                'success': False,
                'message': 'SMS notifications are disabled'
            }), 400
        
        # Send test SMS
        success = config.send_test_sms()
        if success:
            return jsonify({
                'success': True,
                'message': 'Test SMS sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test SMS'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing SMS: {str(e)}'
        }), 500 