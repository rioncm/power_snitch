#!/usr/bin/env python3
"""
Power Snitch Dashboard Blueprint
Handles the main dashboard and related views.
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from web.models.ups import UPS
from web.models.alert import Alert
from web.models.notification import NotificationService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Display the main dashboard."""
    # Get current UPS status
    ups = UPS.get_current_status()
    
    # Get battery history
    battery_history = ups.get_battery_history(limit=24)
    
    # Get recent alerts
    recent_alerts = Alert.get_recent_alerts(limit=10)
    
    # Get notification service status
    notifications = {
        'webhook': NotificationService.get_webhook_config(),
        'email': NotificationService.get_email_config(),
        'sms': NotificationService.get_sms_config()
    }
    
    return render_template('dashboard/index.html',
                         ups=ups,
                         battery_history=battery_history,
                         recent_alerts=recent_alerts,
                         notifications=notifications)

@dashboard_bp.route('/api/status')
@login_required
def get_status():
    """Get current UPS status as JSON."""
    ups = UPS.get_current_status()
    return jsonify(ups.to_dict())

@dashboard_bp.route('/api/battery-history')
@login_required
def get_battery_history():
    """Get battery history as JSON."""
    ups = UPS.get_current_status()
    history = ups.get_battery_history(limit=24)
    return jsonify([entry.to_dict() for entry in history])

@dashboard_bp.route('/api/recent-alerts')
@login_required
def get_recent_alerts():
    """Get recent alerts as JSON."""
    alerts = Alert.get_recent_alerts(limit=10)
    return jsonify([alert.to_dict() for alert in alerts]) 