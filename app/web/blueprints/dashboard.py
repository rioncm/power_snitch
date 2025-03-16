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
from web.models.web_interface import WebInterface
from web.extensions import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Display the dashboard."""
    with db.session_scope() as session:
        web_interface = WebInterface.get_config(session=session)
        return render_template('dashboard.html', 
                            ups=None,
                            config={'web_interface': web_interface.to_dict()})

# Comment out other routes for now - they'll be fixed later
"""
@dashboard_bp.route('/api/status')
@login_required
def get_status():
    # Temporarily disabled
    pass

@dashboard_bp.route('/api/battery-history')
@login_required
def get_battery_history():
    # Temporarily disabled
    pass

@dashboard_bp.route('/api/recent-alerts')
@login_required
def get_recent_alerts():
    # Temporarily disabled
    pass
""" 