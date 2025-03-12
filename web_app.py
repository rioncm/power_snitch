#!/usr/bin/env python3
"""
Power Snitch Web Interface
A Flask web application for monitoring UPS status and managing notifications.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/power_snitch/web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database
db = Database('/opt/power_snitch/data/power_snitch.db')

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
@login_required
def index():
    """Render the dashboard."""
    try:
        # Get current UPS status
        status_file = '/opt/power_snitch/data/status.json'
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)
        else:
            status = {
                'status': 'Unknown',
                'model': 'Unknown',
                'serial': 'Unknown',
                'firmware': 'Unknown',
                'battery': {
                    'charge': 0,
                    'runtime': 0,
                    'temperature': 0,
                    'voltage': 0
                },
                'input': {
                    'voltage': 0,
                    'frequency': 0,
                    'current': 0,
                    'power': 0
                },
                'output': {
                    'voltage': 0,
                    'frequency': 0,
                    'current': 0,
                    'power': 0
                }
            }

        # Get battery health history
        battery_history = db.get_battery_health_history(limit=24)  # Last 24 records
        timestamps = [record.timestamp.strftime('%Y-%m-%d %H:%M:%S') for record in battery_history]
        charges = [record.charge for record in battery_history]

        # Get recent alerts
        alerts = db.get_recent_alerts(limit=10)

        return render_template('dashboard.html',
                             status=status,
                             battery_history={'timestamps': timestamps, 'charges': charges},
                             alerts=alerts)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return render_template('dashboard.html',
                             status={},
                             battery_history={'timestamps': [], 'charges': []},
                             alerts=[])

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Handle settings page."""
    if request.method == 'POST':
        try:
            # Update web interface settings
            web_interface = request.form.get('web_interface', {})
            if web_interface.get('password'):
                db.update_web_interface(
                    port=int(web_interface.get('port', 5000)),
                    password=web_interface.get('password')
                )
            else:
                db.update_web_interface(
                    port=int(web_interface.get('port', 5000))
                )

            # Update UPS configuration
            ups = request.form.get('ups', {})
            db.update_ups_config(
                name=ups.get('name'),
                description=ups.get('description'),
                poll_interval=int(ups.get('poll_interval', 60))
            )

            # Update notification settings
            notifications = request.form.get('notifications', {})
            
            # Webhook
            webhook = notifications.get('webhook', {})
            if webhook.get('enabled'):
                db.update_webhook_config(
                    url=webhook.get('url'),
                    method=webhook.get('method', 'POST'),
                    timeout=int(webhook.get('timeout', 30))
                )
            else:
                db.disable_webhook()

            # Email
            email = notifications.get('email', {})
            if email.get('enabled'):
                smtp = email.get('smtp', {})
                db.update_email_config(
                    smtp_host=smtp.get('host'),
                    smtp_port=int(smtp.get('port', 587)),
                    smtp_username=smtp.get('username'),
                    smtp_password=smtp.get('password'),
                    smtp_use_tls=smtp.get('use_tls') == 'on'
                )
            else:
                db.disable_email()

            # SMS
            sms = notifications.get('sms', {})
            if sms.get('enabled'):
                twilio = sms.get('twilio', {})
                db.update_sms_config(
                    account_sid=twilio.get('account_sid'),
                    auth_token=twilio.get('auth_token'),
                    from_number=twilio.get('from_number')
                )
            else:
                db.disable_sms()

            flash('Settings updated successfully', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            flash('Error updating settings', 'error')
            return redirect(url_for('settings'))

    # Get current configuration
    config = {
        'web_interface': db.get_web_interface(),
        'ups': db.get_ups_config(),
        'notifications': {
            'webhook': db.get_webhook_config(),
            'email': db.get_email_config(),
            'sms': db.get_sms_config()
        }
    }
    return render_template('settings.html', config=config)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login."""
    if request.method == 'POST':
        password = request.form.get('password')
        web_interface = db.get_web_interface()
        
        if check_password_hash(web_interface.password_hash, password):
            user = User(1)  # We only have one user
            login_user(user)
            
            # Check if setup is completed
            if not web_interface.setup_completed:
                return redirect(url_for('setup'))
            return redirect(url_for('index'))
        
        flash('Invalid password', 'error')
    return render_template('login.html')

@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Handle initial setup."""
    web_interface = db.get_web_interface()
    if web_interface.setup_completed:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Update web interface settings
            web_interface = request.form.get('web_interface', {})
            db.update_web_interface(
                port=int(web_interface.get('port', 5000)),
                password=web_interface.get('password'),
                setup_completed=True
            )

            # Update UPS configuration
            ups = request.form.get('ups', {})
            db.update_ups_config(
                name=ups.get('name'),
                description=ups.get('description'),
                poll_interval=int(ups.get('poll_interval', 60))
            )

            # Update notification settings
            notifications = request.form.get('notifications', {})
            
            # Webhook
            webhook = notifications.get('webhook', {})
            if webhook.get('enabled'):
                db.update_webhook_config(
                    url=webhook.get('url'),
                    method=webhook.get('method', 'POST'),
                    timeout=int(webhook.get('timeout', 30))
                )

            # Email
            email = notifications.get('email', {})
            if email.get('enabled'):
                smtp = email.get('smtp', {})
                db.update_email_config(
                    smtp_host=smtp.get('host'),
                    smtp_port=int(smtp.get('port', 587)),
                    smtp_username=smtp.get('username'),
                    smtp_password=smtp.get('password'),
                    smtp_use_tls=smtp.get('use_tls') == 'on'
                )

            # SMS
            sms = notifications.get('sms', {})
            if sms.get('enabled'):
                twilio = sms.get('twilio', {})
                db.update_sms_config(
                    account_sid=twilio.get('account_sid'),
                    auth_token=twilio.get('auth_token'),
                    from_number=twilio.get('from_number')
                )

            flash('Setup completed successfully', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error during setup: {str(e)}")
            flash('Error during setup', 'error')
            return redirect(url_for('setup'))

    # Get current configuration
    config = {
        'web_interface': db.get_web_interface(),
        'ups': db.get_ups_config(),
        'notifications': {
            'webhook': db.get_webhook_config(),
            'email': db.get_email_config(),
            'sms': db.get_sms_config()
        }
    }
    return render_template('setup.html', config=config)

@app.route('/logout')
@login_required
def logout():
    """Handle logout."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/status')
@login_required
def get_status():
    """API endpoint for getting current UPS status."""
    try:
        status_file = '/opt/power_snitch/data/status.json'
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({'error': 'Status file not found'})
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)})

def start_web_interface():
    """Start the web interface."""
    web_interface = db.get_web_interface()
    app.run(host='0.0.0.0', port=web_interface.port)

if __name__ == '__main__':
    start_web_interface() 