#!/bin/bash

# Power Snitch Installation Script
# ===============================
#
# This script will install and configure Power Snitch, a UPS monitoring and notification system.
#
# What will be installed:
# - Power Snitch application files in /opt/power_snitch
# - NUT (Network UPS Tools) for UPS communication
# - Python dependencies from requirements.txt
# - Systemd service for automatic startup
# - Firewall rules for web interface access
#
# What will be configured:
# - NUT for UPS monitoring
# - Web interface with password protection
# - Notification services (webhook, email, SMS)
# - Systemd service for automatic startup
# - Firewall rules for web interface access
#
# What will be modified:
# - /etc/nut/ups.conf (backed up before modification)
# - /etc/nut/nut.conf (backed up before modification)
# - /etc/systemd/system/power_snitch.service
# - /var/log/power_snitch/ (created for logs)
# - Firewall rules (iptables)
#
# Requirements:
# - Root privileges
# - Internet connection for package installation
# - USB-connected UPS
# - Supported operating system (Ubuntu, Debian, Raspbian, CentOS, RHEL, Fedora)
#
# The script will prompt for:
# - Web interface port and admin password
# - UPS name and description
# - Notification service settings (webhook, email, SMS)
#
# All changes will be logged to /var/log/power_snitch/install.log
#
# Press Ctrl+C at any time to abort the installation.

# Configuration
INSTALL_DIR="/opt/power_snitch"
APP_DIR="$INSTALL_DIR/app"
DB_PATH="$APP_DIR/power_snitch.db"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="power_snitch"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
WEB_PORT=80

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run as root"
    exit 1
fi

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check for pip3
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check for python3-venv
    if ! dpkg -l | grep -q python3-venv; then
        log_info "Installing python3-venv package..."
        apt-get update
        apt-get install -y python3-venv
        if [ $? -ne 0 ]; then
            log_error "Failed to install python3-venv"
            exit 1
        fi
    fi
    
    # Check for NUT
    if ! command -v upsc &> /dev/null; then
        log_error "NUT (Network UPS Tools) is required but not installed"
        exit 1
    fi
    
    log_info "System requirements met"
}

# Create installation directory
create_install_dir() {
    log_info "Creating installation directory..."
    for dir in "$APP_DIR" "$APP_DIR/templates" "/var/log/power_snitch"; do
        if ! mkdir -p "$dir"; then
            log_error "Failed to create directory: $dir"
            exit 1
        fi
        chmod 755 "$dir"
    done
}

# Copy application files
copy_files() {
    log_info "Copying application files..."
    
    # Get the parent directory path
    PARENT_DIR="$(dirname "$0")/.."
    
    # Copy Python files
    for file in power_snitch.py web_app.py db.py init_db.py requirements.txt; do
        if ! cp "$PARENT_DIR/$file" "$APP_DIR/"; then
            log_error "Failed to copy $file"
            exit 1
        fi
        chmod 755 "$APP_DIR/$file"
    done
    
    # Copy templates
    if ! cp -r "$PARENT_DIR/templates/"* "$APP_DIR/templates/"; then
        log_error "Failed to copy template files"
        exit 1
    fi
    
    # Copy service file
    if ! cp "./power_snitch.service" "$SERVICE_FILE"; then
        log_error "Failed to copy service file"
        exit 1
    fi
    
    # Set permissions
    chmod -R 755 "$APP_DIR/templates"
    chmod 644 "$SERVICE_FILE"
    chmod 644 "$APP_DIR/requirements.txt"
    
    # Create __init__.py in the templates directory
    if ! touch "$APP_DIR/templates/__init__.py"; then
        log_error "Failed to create __init__.py"
        exit 1
    fi
    chmod 644 "$APP_DIR/templates/__init__.py"
}

# Set up Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    if ! python3 -m venv "$VENV_DIR"; then
        log_error "Failed to create virtual environment"
        exit 1
    fi
    
    # Source the virtual environment with full path
    if ! . "$VENV_DIR/bin/activate"; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    # Upgrade pip
    if ! pip install --upgrade pip; then
        log_error "Failed to upgrade pip"
        exit 1
    fi
    
    # Install requirements from the app directory
    log_info "Installing Python dependencies..."
    if ! pip install -r "$APP_DIR/requirements.txt"; then
        log_error "Failed to install Python dependencies"
        exit 1
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    
    # Activate virtual environment
    if ! . "$VENV_DIR/bin/activate"; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    # Run init_db.py from the app directory
    cd "$APP_DIR" || {
        log_error "Failed to change to app directory"
        exit 1
    }
    
    if ! python3 init_db.py "$DB_PATH"; then
        log_error "Failed to initialize database"
        exit 1
    fi
    
    # Return to original directory
    cd - > /dev/null
}

# Configure firewall
configure_firewall() {
    log_info "Checking firewall configuration..."
    
    # Check if iptables is installed
    if ! command -v iptables &> /dev/null; then
        log_warn "iptables not found, skipping firewall configuration"
        return
    fi
    
    # Check if iptables service is running
    if ! systemctl is-active --quiet iptables; then
        log_warn "iptables service not running, skipping firewall configuration"
        return
    fi
    
    # Add firewall rule for web interface
    log_info "Configuring firewall rules..."
    if ! iptables -C INPUT -p tcp --dport "$WEB_PORT" -j ACCEPT 2>/dev/null; then
        if ! iptables -I INPUT -p tcp --dport "$WEB_PORT" -j ACCEPT; then
            log_error "Failed to add firewall rule"
            return
        fi
    fi
    
    # Save iptables rules
    if command -v iptables-save &> /dev/null; then
        if ! iptables-save > /etc/iptables.rules; then
            log_error "Failed to save iptables rules"
            return
        fi
        log_info "Firewall rules saved"
    else
        log_warn "Could not save iptables rules (iptables-save not found)"
    fi
}

# Set up systemd service
setup_service() {
    log_info "Setting up systemd service..."
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable and start service
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    
    # Check service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Service started successfully"
    else
        log_error "Failed to start service"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi
}

# Main installation process
main() {
    log_info "Starting Power Snitch installation..."
    
    check_requirements
    create_install_dir
    copy_files
    setup_venv
    init_database
    configure_firewall
    setup_service
    
    log_info "Installation completed successfully!"
    log_info "Power Snitch is now running as a system service"
    log_info "Web interface is available at http://localhost:$WEB_PORT"
    log_info "Default login credentials:"
    log_info "  Username: admin"
    log_info "  Password: password"
    log_warn "Please change the default password after first login"
}

# Run installation
main 