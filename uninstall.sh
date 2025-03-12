#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root"
    exit 1
fi

# Stop and disable the service
print_status "Stopping Power Snitch service..."
systemctl stop power_snitch 2>/dev/null || true
systemctl disable power_snitch 2>/dev/null || true

# Remove service file
print_status "Removing systemd service..."
rm -f /etc/systemd/system/power_snitch.service
systemctl daemon-reload

# Remove application files
print_status "Removing application files..."
rm -rf /opt/power_snitch

# Remove log directory
print_status "Removing log files..."
rm -rf /var/log/power_snitch

# Remove status file if it exists
if [ -f /opt/power_snitch/status.json ]; then
    rm -f /opt/power_snitch/status.json
fi

# Remove firewall rule
print_status "Removing firewall rule..."
if command -v iptables &> /dev/null; then
    if iptables -C INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null; then
        iptables -D INPUT -p tcp --dport 8080 -j ACCEPT
        
        # Save iptables rules based on OS
        if command -v netfilter-persistent &> /dev/null; then
            netfilter-persistent save
        elif [ -f /etc/redhat-release ]; then
            service iptables save
        fi
    fi
fi

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