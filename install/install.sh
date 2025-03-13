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
DATA_DIR="$INSTALL_DIR/data"
DB_PATH="$DATA_DIR/power_snitch.db"
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
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 7 ]); then
        log_error "Python 3.7 or higher is required. Found version $PYTHON_VERSION"
        exit 1
    fi
    
    # Check for pip3
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check for NUT
    if ! command -v upsc &> /dev/null; then
        log_info "Installing NUT package..."
        apt-get update
        apt-get install -y nut nut-server nut-client
        if [ $? -ne 0 ]; then
            log_error "Failed to install NUT"
            exit 1
        fi
    fi
    
    # Check for iptables
    if command -v iptables &> /dev/null; then
        log_info "iptables found, checking for iptables-persistent..."
        if ! dpkg -l | grep -q iptables-persistent; then
            log_info "Installing iptables-persistent..."
            DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
            if [ $? -ne 0 ]; then
                log_warn "Failed to install iptables-persistent. Please check your firewall configuration manually."
            fi
        fi
    else
        log_warn "iptables not found. Please check if another firewall is installed and configure it manually."
    fi
    
    log_info "System requirements met"
}

# Create installation directories
create_install_dirs() {
    log_info "Creating installation directories..."
    
    # Create main directories
    for dir in "$INSTALL_DIR" "$INSTALL_DIR/data" "/var/log/power_snitch"; do
        if ! mkdir -p "$dir"; then
            log_error "Failed to create directory: $dir"
            exit 1
        fi
        chmod 755 "$dir"
    done
    
    # Create NUT configuration directory if it doesn't exist
    if ! mkdir -p /etc/nut; then
        log_error "Failed to create NUT configuration directory"
        exit 1
    fi
}

# Copy application files
copy_files() {
    log_info "Copying application files..."
    
    # Get the parent directory path (two levels up from install.sh)
    PARENT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
    
    # Debug output
    log_info "Source directory: $PARENT_DIR"
    
    # Copy Python files
    for file in power_snitch.py web_app.py db.py; do
        if [ ! -f "$PARENT_DIR/$file" ]; then
            log_error "Source file not found: $PARENT_DIR/$file"
            exit 1
        fi
        if ! cp "$PARENT_DIR/$file" "$INSTALL_DIR/"; then
            log_error "Failed to copy $file"
            exit 1
        fi
        chmod 755 "$INSTALL_DIR/$file"
    done
    
    # Copy requirements.txt
    if [ ! -f "$PARENT_DIR/requirements.txt" ]; then
        log_error "Source file not found: $PARENT_DIR/requirements.txt"
        exit 1
    fi
    if ! cp "$PARENT_DIR/requirements.txt" "$INSTALL_DIR/"; then
        log_error "Failed to copy requirements.txt"
        exit 1
    fi
    
    # Copy init_db.py and SQL files
    for file in init_db.py tables.sql defaults.sql; do
        if [ ! -f "$(dirname "$0")/$file" ]; then
            log_error "Source file not found: $(dirname "$0")/$file"
            exit 1
        fi
        if ! cp "$(dirname "$0")/$file" "$INSTALL_DIR/"; then
            log_error "Failed to copy $file"
            exit 1
        fi
    done
    
    # Copy templates directory
    if [ ! -d "$PARENT_DIR/templates" ]; then
        log_error "Templates directory not found: $PARENT_DIR/templates"
        exit 1
    fi
    if ! cp -r "$PARENT_DIR/templates" "$INSTALL_DIR/"; then
        log_error "Failed to copy templates directory"
        exit 1
    fi
    
    # Copy static directory
    if [ ! -d "$PARENT_DIR/static" ]; then
        log_error "Static directory not found: $PARENT_DIR/static"
        exit 1
    fi
    if ! cp -r "$PARENT_DIR/static" "$INSTALL_DIR/"; then
        log_error "Failed to copy static directory"
        exit 1
    fi
    
    # Copy service files
    for service in power_snitch.service power_snitch_web.service; do
        if [ ! -f "$(dirname "$0")/$service" ]; then
            log_error "Source file not found: $(dirname "$0")/$service"
            exit 1
        fi
        if ! cp "$(dirname "$0")/$service" "/etc/systemd/system/"; then
            log_error "Failed to copy service file: $service"
            exit 1
        fi
        chmod 644 "/etc/systemd/system/$service"
    done
    
    # Set permissions
    chmod 644 "$INSTALL_DIR/requirements.txt"
    chmod 644 "$INSTALL_DIR/tables.sql"
    chmod 644 "$INSTALL_DIR/defaults.sql"
    chmod 755 "$INSTALL_DIR/init_db.py"
    chmod -R 755 "$INSTALL_DIR/templates"
    chmod -R 755 "$INSTALL_DIR/static"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Install requirements system-wide
    if ! pip3 install -r "$INSTALL_DIR/requirements.txt"; then
        log_error "Failed to install Python dependencies"
        exit 1
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    
    # Run init_db.py from the installation directory
    cd "$INSTALL_DIR" || {
        log_error "Failed to change to installation directory"
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
    
    # Install iptables-persistent if not present
    if ! dpkg -l | grep -q iptables-persistent; then
        log_info "Installing iptables-persistent..."
        DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
        if [ $? -ne 0 ]; then
            log_error "Failed to install iptables-persistent"
            return
        fi
    fi
    
    # Check if iptables service is running
    if ! systemctl is-active --quiet iptables; then
        log_info "Starting iptables service..."
        systemctl start iptables
        if [ $? -ne 0 ]; then
            log_error "Failed to start iptables service"
            return
        fi
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
    if ! netfilter-persistent save; then
        log_error "Failed to save iptables rules"
        return
    fi
    log_info "Firewall rules saved"
}

# Enable and start services
enable_services() {
    log_info "Enabling and starting services..."
    
    # Reload systemd to recognize new services
    if ! systemctl daemon-reload; then
        log_error "Failed to reload systemd"
        exit 1
    fi
    
    # Enable and start both services
    for service in power_snitch power_snitch_web; do
        if ! systemctl enable "$service"; then
            log_error "Failed to enable $service"
            exit 1
        fi
        if ! systemctl start "$service"; then
            log_error "Failed to start $service"
            exit 1
        fi
        log_info "$service service started successfully"
    done
}

# Configure NUT
configure_nut() {
    log_info "Configuring NUT..."
    mkdir -p /etc/nut

    # Backup existing configurations
    for conf in ups.conf upsd.conf nut.conf; do
        if [ -f "/etc/nut/$conf" ]; then
            cp "/etc/nut/$conf" "/etc/nut/$conf.backup"
        fi
    done

    # Create minimal NUT configuration
    cat > /etc/nut/nut.conf << 'EOL'
MODE=standalone
EOL

    cat > /etc/nut/ups.conf << 'EOL'
[ups]
driver = usbhid-ups
port = auto
desc = Power Snitch UPS
EOL

    cat > /etc/nut/upsd.conf << 'EOL'
LISTEN 127.0.0.1 3493
LISTEN ::1 3493
MAXAGE 15
EOL

    # Set proper permissions
    chown -R root:root /etc/nut
    chmod 640 /etc/nut/*.conf

    # Disable unnecessary NUT services
    log_info "Configuring NUT services..."
    systemctl disable nut-monitor
    systemctl disable nut-client
    systemctl stop nut-monitor
    systemctl stop nut-client

    # Enable and start NUT server
    log_info "Starting NUT server..."
    systemctl enable nut-server
    systemctl start nut-server

    # Check service status
    if ! systemctl is-active --quiet nut-server; then
        log_error "NUT server service failed to start"
    fi

    # Test NUT connection
    if ! upsc ups >/dev/null 2>&1; then
        log_warn "Initial NUT connection test failed. This is normal if no UPS is connected."
        log_warn "Please connect your UPS and run 'upsc ups' to verify the connection."
    else
        log_info "NUT connection test successful"
    fi
}

# Main installation process
main() {
    log_info "Starting Power Snitch installation..."
    
    check_requirements
    create_install_dirs
    copy_files
    install_dependencies
    init_database
    configure_firewall
    configure_nut
    enable_services
    
    log_info "Installation completed successfully!"
    log_info "You can access the web interface at http://localhost:$WEB_PORT"
    log_info "Default credentials: admin / admin"
    log_info "Please change the default password in the web interface settings."
}

# Run main installation process
main 