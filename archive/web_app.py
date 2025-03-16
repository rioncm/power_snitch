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
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, BooleanField, URLField, SelectField, TextAreaField, FloatField
from wtforms.validators import DataRequired, NumberRange, URL, Email, Optional
from db import Database
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
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
        charges = [record.charge_percentage for record in battery_history]
        
        # Get the most recent battery health record for current status
        current_battery = battery_history[0] if battery_history else None

        # Get recent alerts
        alerts = db.get_recent_alerts(limit=10)

        # Get notification service status
        notifications = {
            'webhook': db.get_webhook_config(),
            'email': db.get_email_config(),
            'sms': db.get_sms_config()
        }

        return render_template('dashboard.html',
                             status=status,
                             battery_history={
                                 'timestamps': timestamps,
                                 'charges': charges,
                                 'energy_stored': current_battery.energy_stored if current_battery else 0,
                                 'energy_full': current_battery.energy_full if current_battery else 0
                             },
                             alerts=alerts,
                             notifications=notifications)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return render_template('dashboard.html',
                             status={},
                             battery_history={'timestamps': [], 'charges': []},
                             alerts=[],
                             notifications={'webhook': None, 'email': None, 'sms': None})

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
                    port=int(web_interface.get('port', 80)),
                    password=web_interface.get('password')
                )
            else:
                db.update_web_interface(
                    port=int(web_interface.get('port', 5000))
                )

            # Update UPS configuration
            ups = request.form.get('ups', {})
            if ups:
                # Extract NUT-specific fields
                nut_fields = {
                    'nut_device_name': ups.get('ups_name'),
                    'nut_driver': ups.get('nut_driver'),
                    'nut_port': ups.get('nut_port'),
                    'nut_username': ups.get('nut_username'),
                    'nut_password': ups.get('nut_password'),
                    'nut_retry_count': int(ups.get('nut_retry_count', 3)),
                    'nut_retry_delay': int(ups.get('nut_retry_delay', 5))
                }
                
                # Update UPS configuration with NUT fields
                db.update_ups_config(
                    name=ups.get('ups_name'),
                    description=ups.get('ups_description'),
                    poll_interval=int(ups.get('ups_poll_interval', 60)),
                    **nut_fields
                )

            # Update notification settings
            notifications = request.form.get('notifications', {})
            
            # Webhook
            webhook = notifications.get('webhook', {})
            if webhook.get('enabled'):
                db.update_webhook_config(
                    url=webhook.get('webhook_url'),
                    method=webhook.get('webhook_method', 'POST'),
                    timeout=int(webhook.get('webhook_timeout', 30))
                )
            else:
                db.disable_webhook()

            # Email
            email = notifications.get('email', {})
            if email.get('enabled'):
                smtp = email.get('smtp', {})
                db.update_email_config(
                    smtp_host=email.get('email_smtp_host'),
                    smtp_port=int(email.get('email_smtp_port', 587)),
                    smtp_username=email.get('email_smtp_username'),
                    smtp_password=email.get('email_smtp_password'),
                    smtp_use_tls=email.get('email_smtp_use_tls') == 'on'
                )
            else:
                db.disable_email()

            # SMS
            sms = notifications.get('sms', {})
            if sms.get('enabled'):
                twilio = sms.get('twilio', {})
                db.update_sms_config(
                    account_sid=sms.get('sms_account_sid'),
                    auth_token=sms.get('sms_auth_token'),
                    from_number=sms.get('sms_from_number')
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
        logger.info(f"Web interface: {web_interface.password_hash}")
        logger.info(f"Password: {password}")
        if check_password_hash(web_interface.password_hash, password):
            user = User(1)  # We only have one user
            login_user(user)
            
            # Check if setup is completed
            if not web_interface.setup_completed:
                return redirect(url_for('setup'))
            return redirect(url_for('index'))
        
        flash('Invalid password', 'error')
    return render_template('login.html')

class SetupForm(FlaskForm):
    # Web Interface Settings
    web_interface_port = IntegerField('Port', validators=[
        DataRequired(),
        NumberRange(min=1, max=65535, message='Port must be between 1 and 65535')
    ])
    web_interface_password = PasswordField('Password', 
        description="Leave blank to keep current password",
        validators=[Optional()])

    # UPS Configuration
    ups_name = StringField('Name', 
        description="Name of the UPS device (used for both Power Snitch and NUT configuration)",
        validators=[DataRequired()])
    ups_description = StringField('Description')
    ups_poll_interval = IntegerField('Poll Interval', validators=[
        DataRequired(),
        NumberRange(min=5, message='Poll interval must be at least 5 seconds')
    ])

    # NUT Configuration
    nut_driver = StringField('Driver', 
        description="NUT driver to use (e.g., usbhid-ups, blazer_ser)",
        validators=[DataRequired()])
    nut_port = StringField('Port', 
        description="Device port (e.g., /dev/usb/hiddev0, auto)",
        validators=[DataRequired()])
    nut_username = StringField('Username', 
        description="NUT server username",
        validators=[DataRequired()])
    nut_password = PasswordField('Password', 
        description="NUT server password",
        validators=[DataRequired()])
    nut_retry_count = IntegerField('Retry Count', 
        description="Number of connection retries",
        validators=[
            DataRequired(),
            NumberRange(min=1, max=10, message='Retry count must be between 1 and 10')
        ])
    nut_retry_delay = IntegerField('Retry Delay', 
        description="Delay between connection retries (seconds)",
        validators=[
            DataRequired(),
            NumberRange(min=1, max=60, message='Retry delay must be between 1 and 60 seconds')
        ])

    # Webhook Settings
    webhook_enabled = BooleanField('Enable Webhook')
    webhook_url = URLField('URL', 
        description="The URL where notifications will be sent",
        validators=[Optional(), URL()])
    webhook_method = SelectField('Method', 
        description="HTTP method to use when sending notifications",
        choices=[('POST', 'POST'), ('GET', 'GET')])
    webhook_timeout = IntegerField('Timeout', 
        description="Maximum time to wait for webhook response (seconds)",
        validators=[Optional(), NumberRange(min=1)])
    webhook_headers = TextAreaField('Headers', 
        description="JSON object of headers to send with webhook (e.g., {\"Authorization\": \"Bearer token\"})",
        validators=[Optional()])

    # Email Settings
    email_enabled = BooleanField('Enable Email')
    email_smtp_host = StringField('SMTP Host',
        description="Hostname of your SMTP server")
    email_smtp_port = IntegerField('SMTP Port', 
        description="Port number of your SMTP server",
        validators=[Optional(), NumberRange(min=1, max=65535)])
    email_smtp_username = StringField('Username',
        description="SMTP server username")
    email_smtp_password = PasswordField('Password',
        description="Leave blank to keep current password",
        validators=[Optional()])
    email_smtp_use_tls = BooleanField('Use TLS',
        description="Enable TLS encryption for SMTP connection")
    email_from_email = StringField('From Email', 
        description="Email address to send notifications from",
        validators=[Optional(), Email()])
    email_recipients = StringField('Recipients',
        description="Comma-separated list of email addresses")

    # SMS Settings
    sms_enabled = BooleanField('Enable SMS')
    sms_account_sid = StringField('Account SID',
        description="Your Twilio Account SID")
    sms_auth_token = StringField('Auth Token',
        description="Your Twilio Auth Token")
    sms_from_number = StringField('From Number',
        description="Your Twilio phone number")
    sms_recipients = StringField('Recipients',
        description="Comma-separated list of phone numbers")

    def validate(self):
        if not super().validate():
            return False

        # Validate NUT configuration
        if not all([self.nut_driver.data, self.nut_port.data, 
                   self.nut_username.data, self.nut_password.data]):
            self.nut_driver.errors.append('All NUT settings are required')
            return False

        # Validate email settings if enabled
        if self.email_enabled.data:
            if not all([self.email_smtp_host.data, self.email_smtp_username.data, 
                       self.email_from_email.data, self.email_recipients.data]):
                self.email_smtp_host.errors.append('All email settings are required when email is enabled')
                return False

        # Validate SMS settings if enabled
        if self.sms_enabled.data:
            if not all([self.sms_account_sid.data, self.sms_auth_token.data, 
                       self.sms_from_number.data]):
                self.sms_account_sid.errors.append('All SMS settings are required when SMS is enabled')
                return False

        # Validate webhook settings if enabled
        if self.webhook_enabled.data:
            if not self.webhook_url.data:
                self.webhook_url.errors.append('Webhook URL is required when webhook is enabled')
                return False

        return True

@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Handle initial setup."""
    logger.debug("Setup route accessed")
    web_interface = db.get_web_interface()
    if web_interface.setup_completed:
        logger.debug("Setup already completed, redirecting to index")
        return redirect(url_for('index'))

    form = SetupForm()
    logger.debug("SetupForm initialized")
    
    # Get current configuration
    config = {
        'web_interface': web_interface,
        'ups': db.get_ups_config(),
        'notifications': {
            'webhook': db.get_webhook_config(),
            'email': db.get_email_config(),
            'sms': db.get_sms_config()
        }
    }
    logger.debug(f"Current configuration loaded: {json.dumps(config, default=str)}")
    
    if request.method == 'GET':
        logger.debug("Processing GET request for setup form")
        # Populate web interface settings
        form.web_interface_port.data = config['web_interface'].port
        logger.debug(f"Web interface port set to: {form.web_interface_port.data}")
        
        # Populate UPS configuration from database
        if config['ups']:
            form.ups_name.data = config['ups'].name
            form.ups_description.data = config['ups'].description
            form.ups_poll_interval.data = config['ups'].poll_interval
            form.nut_driver.data = config['ups'].nut_driver
            form.nut_port.data = config['ups'].nut_port
            form.nut_username.data = config['ups'].nut_username
            form.nut_password.data = config['ups'].nut_password
            form.nut_retry_count.data = config['ups'].nut_retry_count
            form.nut_retry_delay.data = config['ups'].nut_retry_delay
            logger.debug(f"Using existing UPS configuration")
        else:
            logger.error("No UPS configuration found in database")
            flash('Error: No UPS configuration found', 'error')
            return redirect(url_for('index'))
        
        # Populate webhook settings
        webhook_config = config['notifications']['webhook']
        form.webhook_enabled.data = webhook_config is not None
        logger.debug(f"Webhook enabled: {form.webhook_enabled.data}")
        if webhook_config and hasattr(webhook_config, 'url'):
            form.webhook_url.data = webhook_config.url
            form.webhook_method.data = webhook_config.method
            form.webhook_timeout.data = webhook_config.timeout
            if hasattr(webhook_config, 'headers') and webhook_config.headers:
                form.webhook_headers.data = json.dumps(webhook_config.headers, indent=2)
            logger.debug(f"Webhook settings populated: url={form.webhook_url.data}, method={form.webhook_method.data}")
        
        # Populate email settings
        email_config = config['notifications']['email']
        form.email_enabled.data = email_config is not None
        logger.debug(f"Email enabled: {form.email_enabled.data}")
        if email_config:
            form.email_smtp_host.data = email_config.smtp_host
            form.email_smtp_port.data = email_config.smtp_port
            form.email_smtp_username.data = email_config.smtp_username
            form.email_smtp_use_tls.data = email_config.smtp_use_tls
            form.email_from_email.data = email_config.from_email
            form.email_recipients.data = ','.join(email_config.recipients)
            logger.debug(f"Email settings populated: host={form.email_smtp_host.data}, port={form.email_smtp_port.data}")
        
        # Populate SMS settings
        sms_config = config['notifications']['sms']
        form.sms_enabled.data = sms_config is not None
        logger.debug(f"SMS enabled: {form.sms_enabled.data}")
        if sms_config:
            form.sms_account_sid.data = sms_config.account_sid
            form.sms_auth_token.data = sms_config.auth_token
            form.sms_from_number.data = sms_config.from_number
            form.sms_recipients.data = ','.join(sms_config.recipients)
            logger.debug(f"SMS settings populated: account_sid={form.sms_account_sid.data}")

    if request.method == 'POST':
        logger.debug("Processing POST request for setup form")
        logger.debug(f"Form data received: {request.form}")
        
        if form.validate():
            logger.debug("Form validation passed")
            try:
                # Update web interface settings
                logger.debug("Updating web interface settings")
                password_hash = None
                if form.web_interface_password.data:
                    password_hash = generate_password_hash(form.web_interface_password.data)
                    logger.debug("Password hash generated")
                
                db.update_web_interface(
                    port=form.web_interface_port.data,
                    password_hash=password_hash,
                    setup_completed=True
                )
                logger.debug("Web interface settings updated successfully")

                # Update UPS configuration
                logger.debug("Updating UPS configuration")
                db.update_ups_config(
                    name=form.ups_name.data,
                    description=form.ups_description.data,
                    poll_interval=form.ups_poll_interval.data,
                    nut_driver=form.nut_driver.data,
                    nut_port=form.nut_port.data,
                    nut_username=form.nut_username.data,
                    nut_password=form.nut_password.data,
                    nut_retry_count=form.nut_retry_count.data,
                    nut_retry_delay=form.nut_retry_delay.data
                )

                # Update notification settings
                if form.webhook_enabled.data:
                    logger.debug("Processing webhook configuration")
                    headers = {}
                    if form.webhook_headers.data:
                        try:
                            headers = json.loads(form.webhook_headers.data)
                            logger.debug(f"Webhook headers parsed: {headers}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid webhook headers JSON: {e}")
                            form.webhook_headers.errors.append('Invalid JSON format')
                            return render_template('setup.html', form=form, config=config)
                    
                    db.update_notification_service('webhook', enabled=True, webhook_config={
                        'url': form.webhook_url.data,
                        'method': form.webhook_method.data,
                        'timeout': form.webhook_timeout.data,
                        'headers': headers
                    })
                else:
                    logger.debug("Disabling webhook")
                    db.update_notification_service('webhook', enabled=False)

                if form.email_enabled.data:
                    logger.debug("Processing email configuration")
                    email_config = {
                        'smtp_host': form.email_smtp_host.data,
                        'smtp_port': form.email_smtp_port.data,
                        'smtp_username': form.email_smtp_username.data,
                        'smtp_password': form.email_smtp_password.data if form.email_smtp_password.data else None,
                        'use_tls': form.email_smtp_use_tls.data,
                        'from_email': form.email_from_email.data,
                        'recipients': form.email_recipients.data.split(',')
                    }
                    logger.debug(f"Email config prepared: {json.dumps({k: v for k, v in email_config.items() if k != 'smtp_password'})}")
                    
                    is_valid, error_msg = validate_email_config(email_config)
                    if not is_valid:
                        logger.error(f"Email validation failed: {error_msg}")
                        flash(error_msg, 'error')
                        return render_template('setup.html', form=form, config=config)
                    logger.debug("Email validation passed")
                    db.update_notification_service('email', enabled=True, email_config=email_config)
                else:
                    logger.debug("Disabling email")
                    db.update_notification_service('email', enabled=False)

                if form.sms_enabled.data:
                    logger.debug("Processing SMS configuration")
                    sms_config = {
                        'account_sid': form.sms_account_sid.data,
                        'auth_token': form.sms_auth_token.data if form.sms_auth_token.data != "********" else None,
                        'from_number': form.sms_from_number.data,
                        'recipients': form.sms_recipients.data.split(',')
                    }
                    logger.debug(f"SMS config prepared: {json.dumps({k: v for k, v in sms_config.items() if k != 'auth_token'})}")
                    db.update_notification_service('sms', enabled=True, sms_config=sms_config)
                else:
                    logger.debug("Disabling SMS")
                    db.update_notification_service('sms', enabled=False)

                logger.info("Setup completed successfully")
                flash('Setup completed successfully', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Error during setup: {str(e)}", exc_info=True)
                flash('Error during setup', 'error')
                return redirect(url_for('setup'))
        else:
            logger.error(f"Form validation failed. Errors: {form.errors}")
            return render_template('setup.html', form=form, config=config)

    return render_template('setup.html', form=form, config=config)

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

@app.route('/api/settings/web_interface', methods=['POST'])
@login_required
def update_web_interface_settings():
    """Handle AJAX web interface settings update."""
    try:
        port = request.form.get('web_interface_port')
        password = request.form.get('web_interface_password')
        
        if not port:
            return jsonify({'success': False, 'error': 'Port is required'}), 400
            
        # Update web interface settings
        if password:
            password_hash = generate_password_hash(password)
            db.update_web_interface(
                port=int(port),
                password_hash=password_hash
            )
        else:
            db.update_web_interface(
                port=int(port)
            )
            
        return jsonify({'success': True, 'message': 'Web interface settings updated successfully'})
    except Exception as e:
        logger.error(f"Error updating web interface settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/ups', methods=['POST'])
@login_required
def update_ups_settings():
    """Handle AJAX UPS settings update."""
    try:
        # Extract NUT-specific fields
        nut_fields = {
            'nut_device_name': request.form.get('ups_name'),
            'nut_driver': request.form.get('nut_driver'),
            'nut_port': request.form.get('nut_port'),
            'nut_username': request.form.get('nut_username'),
            'nut_password': request.form.get('nut_password'),
            'nut_retry_count': int(request.form.get('nut_retry_count', 3)),
            'nut_retry_delay': int(request.form.get('nut_retry_delay', 5))
        }
        
        # Update UPS configuration with NUT fields
        db.update_ups_config(
            name=request.form.get('ups_name'),
            description=request.form.get('ups_description'),
            poll_interval=int(request.form.get('ups_poll_interval', 60)),
            **nut_fields
        )
            
        return jsonify({'success': True, 'message': 'UPS settings updated successfully'})
    except Exception as e:
        logger.error(f"Error updating UPS settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/webhook', methods=['POST'])
@login_required
def update_webhook_settings():
    try:
        # Get form data
        enabled = request.form.get('webhook_enabled') == 'on'
        url = request.form.get('webhook_url')
        method = request.form.get('webhook_method', 'POST')
        timeout = int(request.form.get('webhook_timeout', 10))
        headers = request.form.get('webhook_headers', '{}')
        
        # Validate headers JSON
        try:
            headers_dict = json.loads(headers)
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'error': 'Invalid headers format. Must be valid JSON.'
            }), 400
        
        # Update webhook settings
        config = Config.get_instance()
        webhook_config = {
            'enabled': enabled,
            'url': url,
            'method': method,
            'timeout': timeout,
            'headers': headers_dict
        }
        
        config.set('notifications.webhook', webhook_config)
        config.save()
        
        return jsonify({
            'success': True,
            'message': 'Webhook settings updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings/email', methods=['POST'])
@login_required
def update_email_settings():
    """Handle AJAX email settings update."""
    try:
        enabled = request.form.get('email_enabled') == 'on'
        
        if not enabled:
            db.update_notification_service('email', enabled=False)
            return jsonify({'success': True, 'message': 'Email notifications disabled successfully'})
            
        # Validate required fields
        required_fields = ['email_smtp_host', 'email_smtp_port', 'email_smtp_username', 
                         'email_from_email', 'email_recipients']
        for field in required_fields:
            if not request.form.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Validate email configuration
        email_config = {
            'smtp_host': request.form.get('email_smtp_host'),
            'smtp_port': int(request.form.get('email_smtp_port')),
            'smtp_username': request.form.get('email_smtp_username'),
            'smtp_password': request.form.get('email_smtp_password'),
            'use_tls': request.form.get('email_smtp_use_tls') == 'on',
            'from_email': request.form.get('email_from_email'),
            'recipients': request.form.get('email_recipients').split(',')
        }
        
        is_valid, error_msg = validate_email_config(email_config)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Update email configuration
        db.update_notification_service('email', enabled=True, email_config=email_config)
            
        return jsonify({'success': True, 'message': 'Email settings updated successfully'})
    except Exception as e:
        logger.error(f"Error updating email settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/sms', methods=['POST'])
@login_required
def update_sms_settings():
    """Handle AJAX SMS settings update."""
    try:
        enabled = request.form.get('sms_enabled') == 'on'
        
        if not enabled:
            db.update_notification_service('sms', enabled=False)
            return jsonify({'success': True, 'message': 'SMS notifications disabled successfully'})
            
        # Validate required fields
        required_fields = ['sms_account_sid', 'sms_auth_token', 'sms_from_number']
        for field in required_fields:
            if not request.form.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Update SMS configuration
        sms_config = {
            'account_sid': request.form.get('sms_account_sid'),
            'auth_token': request.form.get('sms_auth_token'),
            'from_number': request.form.get('sms_from_number')
        }
        
        db.update_notification_service('sms', enabled=True, sms_config=sms_config)
            
        return jsonify({'success': True, 'message': 'SMS settings updated successfully'})
    except Exception as e:
        logger.error(f"Error updating SMS settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/complete', methods=['POST'])
@login_required
def complete_setup():
    try:
        # Update the completed flag in the database
        config = Config.get_instance()
        config.set('setup_completed', True)
        config.save()
        
        return jsonify({
            'success': True,
            'message': 'Setup completed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def start_web_interface():
    """Start the web interface."""
    web_interface = db.get_web_interface()
    app.run(host='0.0.0.0', port=web_interface.port, debug=True)

def validate_email_config(config):
    """Validate email configuration."""
    logger.debug(f"Starting email config validation with config: {json.dumps({k: v for k, v in config.items() if k != 'smtp_password'})}")
    
    if not config:
        logger.error("Email configuration is empty")
        return False, "Email configuration is required"
    
    # Validate hostname (allows subdomains)
    if not config.get('smtp_host'):
        logger.error("SMTP host is missing")
        return False, "SMTP host is required"
    
    # More permissive pattern that allows common SMTP hostname formats
    hostname_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-_.]*[a-zA-Z0-9](\.[a-zA-Z]{2,})+$'
    host = config['smtp_host']
    logger.debug(f"Validating SMTP host: {host}")
    logger.debug(f"Using pattern: {hostname_pattern}")
    
    if not re.match(hostname_pattern, host):
        logger.error(f"Hostname validation failed for: {host}")
        return False, "Invalid SMTP host format"
    logger.debug("Hostname validation passed")
    
    # Validate port
    if not config.get('smtp_port'):
        logger.error("SMTP port is missing")
        return False, "SMTP port is required"
    try:
        port = int(config['smtp_port'])
        if not (1 <= port <= 65535):
            logger.error(f"Invalid SMTP port: {port}")
            return False, "Invalid SMTP port"
        logger.debug(f"Port validation passed: {port}")
    except ValueError as e:
        logger.error(f"Port validation error: {e}")
        return False, "Invalid SMTP port"
    
    # Validate from address
    if not config.get('recipients'):
        logger.error("Recipients list is missing")
        return False, "At least one recipient is required"
    if not isinstance(config['recipients'], list):
        logger.error(f"Recipients is not a list: {type(config['recipients'])}")
        return False, "Recipients must be a list"
    if not config['recipients']:
        logger.error("Recipients list is empty")
        return False, "At least one recipient is required"
    for recipient in config['recipients']:
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', recipient):
            logger.error(f"Invalid recipient email address: {recipient}")
            return False, f"Invalid recipient email address: {recipient}"
    logger.debug("Recipients validation passed")
    
    # Username and password are optional
    if config.get('smtp_username') and not config.get('smtp_password'):
        logger.error("Password is missing when username is provided")
        return False, "Password is required when username is provided"
    
    logger.info("Email configuration validation passed successfully")
    return True, None

if __name__ == '__main__':
    start_web_interface() 