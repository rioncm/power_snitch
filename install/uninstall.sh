#!/bin/bash

# Power Snitch Uninstallation Script
# =================================
#
# This script will remove Power Snitch and all its components from the system.
#
# What will be removed:
# - Power Snitch application files from /opt/power_snitch
# - Systemd services (power_snitch and power_snitch_web)
# - Log files from /var/log/power_snitch
# - Firewall rules for web interface
#
# Requirements:
# - Root privileges
#
# Press Ctrl+C at any time to abort the uninstallation.

# Configuration
INSTALL_DIR="/opt/power_snitch"
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

# Stop and remove services
remove_services() {
    log_info "Stopping and removing services..."
    
    # Stop both services
    for service in power_snitch power_snitch_web; do
        if systemctl is-active --quiet "$service"; then
            log_info "Stopping $service service..."
            systemctl stop "$service"
        fi
        if systemctl is-enabled --quiet "$service"; then
            log_info "Disabling $service service..."
            systemctl disable "$service"
        fi
    done
    
    # Remove service files
    for service in power_snitch.service power_snitch_web.service; do
        if [ -f "/etc/systemd/system/$service" ]; then
            log_info "Removing $service..."
            rm -f "/etc/systemd/system/$service"
        fi
    done
    
    # Reload systemd
    systemctl daemon-reload
}

# Remove firewall rules
remove_firewall_rules() {
    log_info "Removing firewall rules..."
    
    # Check if iptables is installed
    if ! command -v iptables &> /dev/null; then
        log_warn "iptables not found, skipping firewall rule removal"
        return
    fi
    
    # Remove web interface port rule
    if iptables -C INPUT -p tcp --dport "$WEB_PORT" -j ACCEPT 2>/dev/null; then
        log_info "Removing web interface port rule..."
        iptables -D INPUT -p tcp --dport "$WEB_PORT" -j ACCEPT
    fi
    
    # Save iptables rules
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save
    fi
}

# Remove application files and directories
remove_files() {
    log_info "Removing application files and directories..."
    
    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        log_info "Removing $INSTALL_DIR..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Remove log directory
    if [ -d "/var/log/power_snitch" ]; then
        log_info "Removing log directory..."
        rm -rf "/var/log/power_snitch"
    fi
}

# Main uninstallation process
main() {
    log_info "Starting Power Snitch uninstallation..."
    
    remove_services
    remove_firewall_rules
    remove_files
    
    log_info "Uninstallation completed successfully!"
    print_status "Uninstallation complete!"
    echo -e "\n${YELLOW}Note:${NC} The following have been preserved:"
    echo "- NUT (Network UPS Tools) installation"
    echo "- Python packages"
    echo "- System packages (iptables, etc.)"
    echo ""
    echo "If you want to remove NUT completely, you can run:"
    echo "sudo apt-get remove nut    # For Debian/Ubuntu"
    echo "sudo yum remove nut        # For RHEL/CentOS"
    echo "sudo dnf remove nut        # For Fedora" 
}

# Run main uninstallation process
main 