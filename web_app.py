from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import threading
import json
import bcrypt
from functools import wraps

def setup_logging():
    log_dir = '/var/log/power_snitch'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'web_interface.log')
    max_bytes = 10 * 1024 * 1024  # 10MB
    backup_count = 5  # Keep 5 backup files

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Set up rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()
app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username

# In-memory user storage (replace with database if needed)
users = {}

def load_user_credentials():
    """Load user credentials from config"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            if 'web_interface' in config and 'credentials' in config['web_interface']:
                creds = config['web_interface']['credentials']
                users[creds['username']] = creds['password']
    except Exception as e:
        logger.error(f"Error loading user credentials: {e}")

@login_manager.user_loader
def load_user(username):
    if username in users:
        return User(username)
    return None

@app.route('/')
@login_required
def index():
    """Dashboard page"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return render_template('dashboard.html', config=config)
    except Exception as e:
        flash(f"Error loading configuration: {e}", 'error')
        return render_template('dashboard.html', config={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        config = load_config()
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not config.get('auth'):
            if username == 'admin' and password == 'admin':
                session['logged_in'] = True
                return redirect(url_for('index'))
        else:
            stored_password = config['auth'].get('password', '').encode('utf-8')
            if (username == config['auth'].get('username') and 
                bcrypt.checkpw(password.encode('utf-8'), stored_password)):
                session['logged_in'] = True
                return redirect(url_for('index'))
        
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    """Configuration page"""
    if request.method == 'POST':
        try:
            new_config = request.get_json()
            with open('config.yaml', 'w') as f:
                yaml.dump(new_config, f)
            flash('Configuration saved successfully', 'success')
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return render_template('config.html', config=config)
    except Exception as e:
        flash(f"Error loading configuration: {e}", 'error')
        return render_template('config.html', config={})

@app.route('/logs')
@login_required
def logs():
    """Log viewer page"""
    try:
        with open('power_snitch.log', 'r') as f:
            logs = f.readlines()[-1000:]  # Last 1000 lines
        return render_template('logs.html', logs=logs)
    except Exception as e:
        flash(f"Error loading logs: {e}", 'error')
        return render_template('logs.html', logs=[])

@app.route('/api/status')
@login_required
def get_status():
    """API endpoint for current UPS status"""
    try:
        status_data = load_status()
        config = load_config()
        
        # Add notification configuration status
        notifications = {
            'webhook': bool(config.get('webhook', {}).get('url')),
            'email': bool(config.get('email', {}).get('smtp_server')),
            'sms': bool(config.get('sms', {}).get('account_sid'))
        }
        
        return jsonify({
            'status': status_data.get('ups_data', {}),
            'ups_status': {
                'connected': status_data.get('connected', False),
                'error': status_data.get('error'),
                'last_successful_check': status_data.get('last_successful_check')
            },
            'notifications': notifications
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def api_config():
    if request.method == 'GET':
        config = load_config()
        # Remove sensitive information
        if 'auth' in config:
            config['auth'].pop('password', None)
        if 'email' in config:
            config['email'].pop('password', None)
        if 'sms' in config:
            config['sms'].pop('auth_token', None)
        return jsonify(config)
    
    elif request.method == 'POST':
        try:
            new_config = request.get_json()
            current_config = load_config()
            
            # Update configuration sections
            for section in ['ups', 'webhook', 'email', 'sms', 'notification_triggers']:
                if section in new_config:
                    current_config[section] = new_config[section]
            
            # Handle password updates
            if 'auth' in new_config and new_config['auth'].get('password'):
                if 'auth' not in current_config:
                    current_config['auth'] = {}
                current_config['auth']['username'] = new_config['auth']['username']
                current_config['auth']['password'] = bcrypt.hashpw(
                    new_config['auth']['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
            
            save_config(current_config)
            return jsonify({'message': 'Configuration updated successfully'})
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
@login_required
def get_logs():
    try:
        log_file = 'power_snitch.log'
        if not os.path.exists(log_file):
            return jsonify({'logs': []})
        
        with open(log_file, 'r') as f:
            logs = f.readlines()
        
        formatted_logs = []
        for log in logs[-1000:]:  # Get last 1000 lines
            try:
                # Parse log entry
                parts = log.split(' - ', 2)
                if len(parts) == 3:
                    timestamp, level, message = parts
                    formatted_logs.append({
                        'timestamp': timestamp.strip(),
                        'level': level.strip(),
                        'message': message.strip()
                    })
            except Exception as e:
                logger.error(f"Error parsing log entry: {e}")
                continue
        
        return jsonify({'logs': formatted_logs})
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/download')
@login_required
def download_logs():
    try:
        return send_file('power_snitch.log',
                        mimetype='text/plain',
                        as_attachment=True,
                        download_name='power_snitch.log')
    except Exception as e:
        logger.error(f"Error downloading logs: {e}")
        return jsonify({'error': str(e)}), 500

def create_default_config():
    """Create default configuration if it doesn't exist"""
    if not os.path.exists('config.yaml'):
        default_config = {
            'web_interface': {
                'credentials': {
                    'username': 'admin',
                    'password': generate_password_hash('admin')
                }
            }
        }
        with open('config.yaml', 'w') as f:
            yaml.dump(default_config, f)

def load_config():
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def save_config(config):
    try:
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

def load_status():
    try:
        with open('status.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error(f"Error loading status: {e}")
        return {}

def start_web_interface():
    """Start the web interface"""
    create_default_config()
    load_user_credentials()
    
    # Load configuration
    config = load_config()
    
    # Get port from config, default to 8080 if not specified
    port = config.get('web_interface', {}).get('port', 8080)
    
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    start_web_interface() 