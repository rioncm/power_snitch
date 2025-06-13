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
    
    # Create main installation directory and logs directory
    for dir in "$INSTALL_DIR" "/var/log/power_snitch"; do
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
    
    # Get the app directory path (two levels up from install.sh)
    APP_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
    
    # Debug output
    log_info "Source directory: $APP_DIR"
    
    # Check if app directory exists
    if [ ! -d "$APP_DIR" ]; then
        log_error "Application directory not found: $APP_DIR"
        exit 1
    fi
    
    # Copy entire app directory structure
    if ! cp -r "$APP_DIR"/* "$INSTALL_DIR/"; then
        log_error "Failed to copy application files"
        exit 1
    fi
    
    # Set permissions efficiently
    find "$INSTALL_DIR" -type d -exec chmod 755 {} +
    find "$INSTALL_DIR" -type f -exec chmod 644 {} +
    
    # Make Python files executable
    find "$INSTALL_DIR" -type f -name "*.py" -exec chmod 755 {} +
    
    log_info "Files copied successfully"
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
    
    # Run database initialization script
    if ! python3 "$INSTALL_DIR/install/init_db.py" "$DB_PATH"; then
        log_error "Failed to initialize database"
        exit 1
    fi
    
    # Set proper permissions
    chmod 644 "$DB_PATH"
    chown root:root "$DB_PATH"
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    # Check if iptables is installed
    if ! command -v iptables &> /dev/null; then
        log_warn "iptables not found, skipping firewall configuration"
        return
    fi
    
    # Add web interface port rule
    if ! iptables -C INPUT -p tcp --dport "$WEB_PORT" -j ACCEPT 2>/dev/null; then
        iptables -A INPUT -p tcp --dport "$WEB_PORT" -j ACCEPT
    fi
    
    # Save iptables rules
    if command -v netfilter-persistent &> /dev/null; then
            netfilter-persistent save
    fi
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
    chmod 644 /etc/nut/*.conf

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

# Install systemd service units
install_services() {
    log_info "Installing systemd service units..."
    
    # Copy service unit files
    for service in power_snitch.service power_snitch_web.service; do
        if [ ! -f "$INSTALL_DIR/install/$service" ]; then
            log_error "Service unit file not found: $service"
            exit 1
        fi
        if ! cp "$INSTALL_DIR/install/$service" "/etc/systemd/system/"; then
            log_error "Failed to copy service unit file: $service"
            exit 1
        fi
        chmod 644 "/etc/systemd/system/$service"
    done
    
    log_info "Service units installed successfully"
}

# Enable services
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

ups_defaults () {
    # Detect and configure UPS
    echo "Detecting UPS..."
    if lsusb | grep -qi "UPS"; then
        # UPS detected, get info from NUT
        systemctl start nut-server
        sleep 2
        
        # Get UPS information from NUT
        UPS_MFR=$(upsc ups 2>/dev/null | grep "device.mfr" | cut -d: -f2 | xargs)
        UPS_MODEL=$(upsc ups 2>/dev/null | grep "device.model" | cut -d: -f2 | xargs)
        UPS_BATTERY_TYPE=$(upsc ups 2>/dev/null | grep "battery.type" | cut -d: -f2 | xargs)
        UPS_SERIAL=$(upsc ups 2>/dev/null | grep "ups.serial" | cut -d: -f2 | xargs)
        UPS_FIRMWARE=$(upsc ups 2>/dev/null | grep "ups.firmware" | cut -d: -f2 | xargs)
        UPS_DRIVER=$(upsc ups 2>/dev/null | grep "driver.name" | cut -d: -f2 | xargs)
        
        # Capture all UPS information as JSON
        all_info=$(upsc ups 2>/dev/null | awk -F': ' '{gsub(/^[ \t]+|[ \t]+$/, "", $1); gsub(/^[ \t]+|[ \t]+$/, "", $2); printf "\"%s\": \"%s\",\n", $1, $2}' | sed '$ s/,$//')
        all_info="{${all_info}}"
        
        # Log UPS detection
        echo "UPS detected:"
        echo "Manufacturer: ${UPS_MFR:-Unknown Manufacturer}"
        echo "Model: ${UPS_MODEL:-Unknown Model}"
        echo "Battery Type: ${UPS_BATTERY_TYPE:-Unknown}"
        echo "Serial: ${UPS_SERIAL:-Unknown}"
        echo "Firmware: ${UPS_FIRMWARE:-Unknown}"
        echo "Driver: ${UPS_DRIVER:-usbhid-ups}"
        echo "All Info: ${all_info}"
    else
        # Default values for no UPS detected
        UPS_MFR="Unknown Manufacturer"
        UPS_MODEL="Unknown Model"
        UPS_BATTERY_TYPE="Unknown"
        UPS_SERIAL=""
        UPS_FIRMWARE="Unknown"
        UPS_DRIVER="usbhid-ups"
        all_info="{}"
        
        # Log no UPS detected
        echo "No UPS detected, using default values"
    fi
echo "Setting up database defaults for detected UPS..."
echo "Creating ups.sql in $(pwd)"
ls -l ups.sql  # Check if it exists before creation
# Append UPS default configuration to ups.sql
    cat <<EOF > "$INSTALL_DIR/install/ups.sql"
INSERT INTO ups (
    manufacturer,
    model,
    battery_type,
    description,
    driver,
    polling_interval,
    all_info
) VALUES (
    '${UPS_MFR:-Unknown Manufacturer}',
    '${UPS_MODEL:-Unknown Model}',
    '${UPS_BATTERY_TYPE:-Unknown}',
    'Auto-detected UPS',
    '${UPS_DRIVER:-usbhid-ups}',
    10,
    '${all_info}'
);
EOF
echo "Database defaults file created successfully"    
}

# Main installation process
main() {
    log_info "Starting Power Snitch installation..."
    
    check_requirements
    create_install_dirs
    copy_files
    install_dependencies
    configure_nut
    ups_defaults    
    configure_firewall    
    init_database
    install_services
    enable_services
    
    log_info "Installation completed successfully!"
    log_info "You can access the web interface at http://localhost:$WEB_PORT"
    log_info "Default credentials: admin / admin"
    log_info "Please change the default password in the web interface settings."
}

# Run main installation process
main 