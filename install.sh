#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handling
set -eE  # Exit on error and error in pipes

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "\n${RED}Installation failed!${NC}"
        
        # Check what might have gone wrong
        if [ ! -f "/etc/nut/ups.conf" ]; then
            echo -e "${YELLOW}NUT configuration file not found. NUT installation may have failed.${NC}"
            echo "Try manually installing NUT: sudo apt-get install nut"
        fi
        
        if [ ! -d "$INSTALL_DIR" ]; then
            echo -e "${YELLOW}Installation directory was not created.${NC}"
            echo "Check if you have sufficient permissions: sudo ls -la /opt"
        fi
        
        if [ ! -f "/etc/systemd/system/power_snitch.service" ]; then
            echo -e "${YELLOW}Service file was not installed.${NC}"
            echo "Try manually copying the service file: sudo cp power_snitch.service /etc/systemd/system/"
        fi
        
        # Add firewall checks
        if ! command -v iptables &> /dev/null; then
            echo -e "${YELLOW}iptables is not installed.${NC}"
            echo "Try installing iptables manually:"
            echo "sudo apt-get install iptables iptables-persistent"
        fi
        
        if ! iptables -C INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null; then
            echo -e "${YELLOW}Firewall rule for web interface is missing.${NC}"
            echo "Try adding the rule manually:"
            echo "sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT"
            echo "sudo netfilter-persistent save"
        fi
        
        echo -e "\n${YELLOW}For troubleshooting:${NC}"
        echo "1. Check the logs above for specific errors"
        echo "2. Ensure all prerequisites are installed"
        echo "3. Verify you have sufficient permissions"
        echo "4. Try running the failed commands manually"
        echo -e "\nFor support, please file an issue with the above output at:"
        echo "https://github.com/yourusername/power_snitch/issues"
    fi
}

# Set up trap for cleanup
trap cleanup EXIT

# Function to print status messages
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

# Function to detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
    else
        OS=$(uname -s)
    fi
}

# Function to install NUT
install_nut() {
    print_status "Installing NUT (Network UPS Tools)..."
    case $OS in
        "Ubuntu"|"Debian GNU/Linux")
            apt-get update
            apt-get install -y nut
            ;;
        "Raspbian GNU/Linux")
            apt-get update
            apt-get install -y nut
            ;;
        "CentOS Linux"|"Red Hat Enterprise Linux")
            yum install -y epel-release
            yum install -y nut
            ;;
        "Fedora")
            dnf install -y nut
            ;;
        *)
            print_error "Unsupported operating system: $OS"
            print_status "Please install NUT manually and run this script again"
            exit 1
            ;;
    esac
}

# Function to check if NUT is installed
check_nut() {
    if ! command -v upsd &> /dev/null; then
        print_status "NUT is not installed"
        install_nut
    else
        print_status "NUT is already installed"
    fi
}

# Function to check Python dependencies
check_python_deps() {
    print_status "Checking Python dependencies..."
    if ! command -v pip3 &> /dev/null; then
        case $OS in
            "Ubuntu"|"Debian GNU/Linux"|"Raspbian GNU/Linux")
                apt-get update
                apt-get install -y python3-pip
                ;;
            "CentOS Linux"|"Red Hat Enterprise Linux"|"Fedora")
                if command -v dnf &> /dev/null; then
                    dnf install -y python3-pip
                else
                    yum install -y python3-pip
                fi
                ;;
        esac
    fi
    
    # Install required Python packages
    pip3 install -r "$INSTALL_DIR/requirements.txt"
}

# Function to verify installation
verify_installation() {
    local has_errors=0
    
    # Check NUT service
    if ! systemctl is-active --quiet nut-server; then
        print_warning "NUT service is not running"
        has_errors=1
    fi
    
    # Check Power Snitch service
    if ! systemctl is-enabled --quiet power_snitch; then
        print_warning "Power Snitch service is not enabled"
        has_errors=1
    fi
    
    # Check log directory permissions
    if [ ! -w "$LOG_DIR" ]; then
        print_warning "Log directory permissions may be incorrect"
        has_errors=1
    fi
    
    # Check configuration file
    if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
        print_warning "Configuration file is missing"
        has_errors=1
    fi
    
    return $has_errors
}

# Function to prompt for UPS description
configure_ups() {
    # Prompt for UPS description
    echo -e "\n${GREEN}UPS Configuration${NC}"
    read -p "Enter a description for your UPS (e.g., 'Office UPS'): " ups_description
    
    # Set default if empty
    if [ -z "$ups_description" ]; then
        ups_description="My UPS"
    fi
    
    # Backup existing ups.conf if it exists
    if [ -f /etc/nut/ups.conf ]; then
        cp /etc/nut/ups.conf /etc/nut/ups.conf.bak
        print_status "Backed up existing ups.conf to ups.conf.bak"
    fi
    
    # Create ups.conf with USB configuration
    cat > /etc/nut/ups.conf << EOF
[ups]
    driver = usbhid-ups
    port = auto
    desc = "${ups_description}"
EOF
    
    print_status "Created UPS configuration with description: ${ups_description}"
    
    # Set correct permissions
    chmod 640 /etc/nut/ups.conf
    chown root:nut /etc/nut/ups.conf
}

# Function to configure config.yaml and notification services
configure_power_snitch() {
    local config_file="$INSTALL_DIR/config.yaml"
    local ups_name="ups"  # This matches the name in ups.conf
    
    # Copy example config first
    print_status "Creating initial configuration from example..."
    cp "$INSTALL_DIR/config.yaml.example" "$config_file"
    
    # Prompt for web interface port
    read -p "Enter web interface port (default: 8080): " WEB_PORT
    WEB_PORT=${WEB_PORT:-8080}
    
    # Validate port number
    if ! [[ "$WEB_PORT" =~ ^[0-9]+$ ]] || [ "$WEB_PORT" -lt 1 ] || [ "$WEB_PORT" -gt 65535 ]; then
        print_error "Invalid port number. Please enter a number between 1 and 65535."
        exit 1
    fi
    
    # Prompt for admin password
    read -s -p "Enter admin password for web interface: " admin_password
    echo
    read -s -p "Confirm admin password: " admin_password_confirm
    echo
    
    if [ "$admin_password" != "$admin_password_confirm" ]; then
        print_error "Passwords do not match!"
        exit 1
    fi
    
    # Hash the password using Python's bcrypt
    print_status "Hashing password..."
    hashed_password=$(python3 -c "
import bcrypt
password = '$admin_password'.encode('utf-8')
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password, salt)
print(hashed.decode('utf-8'))
")
    
    # Update web interface settings
    print_status "Updating web interface settings..."
    awk -v port="$WEB_PORT" -v password="$hashed_password" '
        /web_interface:/ { print; next }
        /  port:/ { print "  port: " port; next }
        /  password:/ { print "  password: \"" password "\""; next }
        { print }
    ' "$config_file" > "$config_file.tmp" && mv "$config_file.tmp" "$config_file"
    
    # Prompt for notification services
    print_status "Configuring notification services..."
    local enabled_services=()
    
    read -p "Enable webhook notifications? (y/N): " enable_webhook
    if [[ $enable_webhook =~ ^[Yy]$ ]]; then
        enabled_services+=("webhook")
        read -p "Enter webhook URL: " webhook_url
        read -p "Enter webhook method (default: POST): " webhook_method
        webhook_method=${webhook_method:-POST}
        read -p "Enter webhook timeout (default: 10): " webhook_timeout
        webhook_timeout=${webhook_timeout:-10}
        
        awk -v url="$webhook_url" -v method="$webhook_method" -v timeout="$webhook_timeout" '
            /webhook:/ { print; next }
            /  enabled:/ { print "  enabled: true"; next }
            /  url:/ { print "  url: \"" url "\""; next }
            /  method:/ { print "  method: " method; next }
            /  timeout:/ { print "  timeout: " timeout; next }
            { print }
        ' "$config_file" > "$config_file.tmp" && mv "$config_file.tmp" "$config_file"
    fi
    
    read -p "Enable email notifications? (y/N): " enable_email
    if [[ $enable_email =~ ^[Yy]$ ]]; then
        enabled_services+=("email")
        read -p "Enter SMTP server: " smtp_host
        read -p "Enter SMTP port (default: 587): " smtp_port
        smtp_port=${smtp_port:-587}
        read -p "Enter SMTP username: " smtp_username
        read -s -p "Enter SMTP password: " smtp_password
        echo
        read -p "Enter sender email: " from_email
        read -p "Enter recipient email: " to_email
        
        awk -v host="$smtp_host" -v port="$smtp_port" -v user="$smtp_username" \
            -v pass="$smtp_password" -v from="$from_email" -v to="$to_email" '
            /email:/ { print; next }
            /  enabled:/ { print "  enabled: true"; next }
            /smtp:/ { print "  smtp:"; next }
            /    host:/ { print "    host: \"" host "\""; next }
            /    port:/ { print "    port: " port; next }
            /    username:/ { print "    username: \"" user "\""; next }
            /    password:/ { print "    password: \"" pass "\""; next }
            /    use_tls:/ { print "    use_tls: true"; next }
            /recipients:/ { print "    recipients: [\"" to "\"]"; next }
            { print }
        ' "$config_file" > "$config_file.tmp" && mv "$config_file.tmp" "$config_file"
    fi
    
    read -p "Enable SMS notifications? (y/N): " enable_sms
    if [[ $enable_sms =~ ^[Yy]$ ]]; then
        enabled_services+=("sms")
        read -p "Enter Twilio Account SID: " twilio_sid
        read -s -p "Enter Twilio Auth Token: " twilio_token
        echo
        read -p "Enter Twilio From Number: " twilio_from
        read -p "Enter recipient phone number: " twilio_to
        
        awk -v sid="$twilio_sid" -v token="$twilio_token" \
            -v from="$twilio_from" -v to="$twilio_to" '
            /sms:/ { print; next }
            /  enabled:/ { print "  enabled: true"; next }
            /twilio:/ { print "  twilio:"; next }
            /    account_sid:/ { print "    account_sid: \"" sid "\""; next }
            /    auth_token:/ { print "    auth_token: \"" token "\""; next }
            /    from_number:/ { print "    from_number: \"" from "\""; next }
            /recipients:/ { print "    recipients: [\"" to "\"]"; next }
            { print }
        ' "$config_file" > "$config_file.tmp" && mv "$config_file.tmp" "$config_file"
    fi
    
    # Update enabled services list
    if [ ${#enabled_services[@]} -gt 0 ]; then
        services_json=$(printf '%s\n' "${enabled_services[@]}" | jq -R . | jq -s .)
        awk -v services="$services_json" '
            /enabled_services:/ { print "  enabled_services: " services; next }
            { print }
        ' "$config_file" > "$config_file.tmp" && mv "$config_file.tmp" "$config_file"
    fi
    
    # Set proper permissions
    chmod 600 "$config_file"
    chown root:root "$config_file"
    
    print_status "Configuration completed successfully!"
}

# Function to install and configure iptables
configure_firewall() {
    print_status "Configuring firewall rules..."
    
    # Check if iptables is installed
    if ! command -v iptables &> /dev/null; then
        print_status "Installing iptables..."
        case $OS in
            "Ubuntu"|"Debian GNU/Linux"|"Raspbian GNU/Linux")
                apt-get update
                apt-get install -y iptables
                ;;
            "CentOS Linux"|"Red Hat Enterprise Linux"|"Fedora")
                if command -v dnf &> /dev/null; then
                    dnf install -y iptables-services
                else
                    yum install -y iptables-services
                fi
                ;;
        esac
    fi
    
    # Install iptables-persistent
    case $OS in
        "Ubuntu"|"Debian GNU/Linux"|"Raspbian GNU/Linux")
            print_status "Installing iptables-persistent..."
            # Pre-seed the debconf database to avoid prompts
            echo "iptables-persistent iptables-persistent/autosave_v4 boolean true" | debconf-set-selections
            echo "iptables-persistent iptables-persistent/autosave_v6 boolean true" | debconf-set-selections
            apt-get install -y iptables-persistent
            ;;
        "CentOS Linux"|"Red Hat Enterprise Linux"|"Fedora")
            systemctl enable iptables
            ;;
    esac
    
    # Add rules for web interface
    print_status "Adding firewall rules for web interface..."
    
    # Check if rule already exists
    if ! iptables -C INPUT -p tcp --dport $WEB_PORT -j ACCEPT 2>/dev/null; then
        # Add rule for web interface
        iptables -I INPUT -p tcp --dport $WEB_PORT -j ACCEPT
        print_status "Added rule for web interface port $WEB_PORT"
    else
        print_status "Rule for web interface port $WEB_PORT already exists"
    fi
    
    # Save rules
    case $OS in
        "Ubuntu"|"Debian GNU/Linux"|"Raspbian GNU/Linux")
            netfilter-persistent save
            systemctl enable netfilter-persistent
            ;;
        "CentOS Linux"|"Red Hat Enterprise Linux"|"Fedora")
            service iptables save
            ;;
    esac
    
    print_status "Firewall configuration completed"
}

# Function to verify firewall configuration
verify_firewall() {
    local has_errors=0
    
    # Check if iptables is running
    if ! iptables -L > /dev/null 2>&1; then
        print_warning "iptables is not running"
        has_errors=1
    fi
    
    # Check if web interface port is open
    if ! iptables -C INPUT -p tcp --dport $WEB_PORT -j ACCEPT 2>/dev/null; then
        print_warning "Web interface port $WEB_PORT is not open in firewall"
        has_errors=1
    fi
    
    # Check if iptables-persistent is installed (Debian-based systems)
    case $OS in
        "Ubuntu"|"Debian GNU/Linux"|"Raspbian GNU/Linux")
            if ! dpkg -l | grep -q iptables-persistent; then
                print_warning "iptables-persistent is not installed"
                has_errors=1
            fi
            ;;
        "CentOS Linux"|"Red Hat Enterprise Linux"|"Fedora")
            if ! systemctl is-enabled --quiet iptables; then
                print_warning "iptables service is not enabled"
                has_errors=1
            fi
            ;;
    esac
    
    return $has_errors
}

# Detect OS
detect_os
print_status "Detected OS: $OS"

# Check and install NUT
check_nut

# Create installation directory
INSTALL_DIR="/opt/power_snitch"
print_status "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Create log directory
LOG_DIR="/var/log/power_snitch"
print_status "Creating log directory..."
mkdir -p "$LOG_DIR"

# Copy application files
print_status "Copying application files..."
cp -r ./* "$INSTALL_DIR/"

# Set permissions
print_status "Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chown -R root:root "$LOG_DIR"
chmod -R 755 "$LOG_DIR"

# Check Python dependencies
check_python_deps


# Configure firewall
print_status "Setting up firewall..."
configure_firewall

# Install systemd service
print_status "Installing systemd service..."
cp "$INSTALL_DIR/power_snitch.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable power_snitch.service

# Configure NUT
print_status "Configuring NUT..."
if [ ! -f /etc/nut/nut.conf.bak ]; then
    cp /etc/nut/nut.conf /etc/nut/nut.conf.bak
fi
echo 'MODE=standalone' > /etc/nut/nut.conf

# Configure UPS
configure_ups

# Configure Power Snitch
print_status "Configuring Power Snitch..."
configure_power_snitch

# Start NUT service
print_status "Starting NUT service..."
systemctl enable nut-server
systemctl restart nut-server

# Verify UPS connection
print_status "Verifying UPS connection..."
sleep 2  # Give NUT a moment to detect the UPS
if upsc ups 2>/dev/null; then
    echo -e "${GREEN}UPS connection successful!${NC}"
else
    echo -e "${YELLOW}Warning: Could not connect to UPS. Please check your USB connection and try:${NC}"
    echo "1. sudo systemctl restart nut-server"
    echo "2. sudo upsc ups"
fi

# Verify firewall configuration
print_status "Verifying firewall configuration..."
verify_firewall

# Verify installation
print_status "Verifying installation..."
if verify_installation; then
    echo -e "\n${GREEN}Installation completed successfully!${NC}"
else
    echo -e "\n${YELLOW}Installation completed with warnings.${NC}"
fi

# Print next steps
echo -e "\n${GREEN}Next steps:${NC}"
echo "1. Configure your UPS in /etc/nut/ups.conf:"
echo -e "   ${YELLOW}Example configuration:${NC}"
echo "   [ups]"
echo "       driver = usbhid-ups"
echo "       port = auto"
echo "       desc = \"Your UPS\""
echo ""
echo "2. Find your UPS driver:"
echo "   sudo nut-scanner -U"
echo ""
echo "3. Test your UPS configuration:"
echo "   sudo upsc ups"
echo ""
echo "4. Start Power Snitch:"
echo "   sudo systemctl start power_snitch"
echo ""
echo "5. Access the web interface:"
echo "   http://$(hostname -I | cut -d' ' -f1):$WEB_PORT"
echo "   Default credentials: admin/admin"
echo ""
echo -e "${YELLOW}Important security notes:${NC}"
echo "- Change the default web interface password immediately"
echo "- Secure your config.yaml file permissions"
echo "- Consider setting up HTTPS with a reverse proxy"
echo ""
echo -e "${GREEN}Useful commands:${NC}"
echo "- Check service status: sudo systemctl status power_snitch"
echo "- View logs: sudo journalctl -u power_snitch -f"
echo "- Configuration file: /opt/power_snitch/config.yaml"
echo "- Log directory: /var/log/power_snitch/"
echo ""
echo -e "${YELLOW}If you encounter any issues:${NC}"
echo "1. Check the logs: tail -f /var/log/power_snitch/*.log"
echo "2. Verify UPS connection: sudo upsc ups"
echo "3. Check service status: sudo systemctl status power_snitch"
echo "4. Review configuration: sudo nano /opt/power_snitch/config.yaml"
echo ""
echo -e "${YELLOW}Firewall Configuration:${NC}"
echo "- Web interface port $WEB_PORT is open in the firewall"
echo "- Firewall rules are persistent across reboots"
echo "- To view current firewall rules: sudo iptables -L"
echo "- To modify rules: edit and then run 'sudo netfilter-persistent save'"
echo ""
echo "For additional help, visit: https://github.com/yourusername/power_snitch" 