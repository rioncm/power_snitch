# Power Snitch

A comprehensive UPS monitoring solution with web interface and multi-channel notifications.

## Features

- Real-time UPS monitoring
- Web-based dashboard
- Multiple notification channels (Webhook, Email, SMS)
- Automatic service management
- Detailed logging with automatic rotation
- Mobile-responsive interface

## Prerequisites

- Python 3.6 or higher
- Network UPS Tools (NUT) - Will be installed by the setup script
- Systemd-based Linux distribution (Ubuntu, Debian, Raspbian, CentOS, RHEL, or Fedora)
- Root/sudo access
- A supported UPS device

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/power_snitch.git
cd power_snitch
```

2. Make the installation script executable:
```bash
chmod +x install.sh
```

3. Run the installation script as root:
```bash
sudo ./install.sh
```

## Configuration

### 1. UPS Configuration

After installation, you need to configure your UPS in `/etc/nut/ups.conf`. Example configuration:

```ini
[ups]
    driver = usbhid-ups
    port = auto
    desc = "APC UPS"
```

To find your UPS driver:
```bash
sudo nut-scanner -U
```

### 2. Application Configuration

Create or edit `config.yaml` in the `/opt/power_snitch` directory:

```yaml
# Web Interface Configuration
web_interface:
  port: 8080  # Port for the web interface
  credentials:
    username: "admin"
    password: "your-secure-password"  # Will be hashed automatically

# UPS Configuration
ups:
  name: "ups"  # The name from ups.conf
  poll_interval: 5  # Seconds between checks
  connection_retry_delay: 5  # Seconds to wait between connection attempts
  max_retries: 3  # Maximum number of connection retries

# Notification Services
webhook:
  enabled: true
  url: "https://your-webhook-url"
  method: "POST"  # HTTP method to use
  timeout: 10  # Timeout in seconds
  headers:
    Authorization: "Bearer your-token"

email:
  enabled: true
  smtp:
    host: "smtp.gmail.com"
    port: 587
    use_tls: true
    username: "your-email@gmail.com"
    password: "your-app-password"
  recipients:
    - "recipient1@example.com"
    - "recipient2@example.com"

sms:
  enabled: true
  twilio:
    account_sid: "your-account-sid"
    auth_token: "your-auth-token"
    from_number: "+1234567890"
  recipients:
    - "+1987654321"

# Notification Triggers
triggers:
  battery_level_change: 5  # Notify on 5% battery change
  load_change: 10  # Notify on 10% load change
  always_notify:
    - low_battery  # Always notify on low battery
    - power_failure  # Always notify on power failure
    - power_restored  # Always notify on power restoration

# List of enabled notification services
enabled_services:
  - webhook
  - email
  - sms
```

**Important Security Notes:**
1. The configuration file (`config.yaml`) should have restricted permissions:
   ```bash
   sudo chmod 600 /opt/power_snitch/config.yaml
   sudo chown root:root /opt/power_snitch/config.yaml
   ```
2. All passwords and tokens in the config file should be strong and unique
3. The web interface should be accessed over HTTPS in production
4. Consider using environment variables for sensitive credentials

## Starting the Service

1. After configuring your UPS, restart the NUT server:
```bash
sudo systemctl restart nut-server
```

2. Test the UPS connection:
```bash
sudo upsc ups
```

3. Start the Power Snitch service:
```bash
sudo systemctl start power_snitch
```

## Web Interface

Access the web interface at `http://your-server:8080` (or your configured port)

Default credentials:
- Username: admin
- Password: admin

**Important**: Change the default password immediately after first login through the web interface.

## Monitoring and Maintenance

### Checking Status
```bash
sudo systemctl status power_snitch
```

### Log Management
The application uses rotating logs to prevent disk space issues. Logs are stored in `/var/log/power_snitch/`:

- Main application log: `power_snitch.log`
- Web interface log: `web_interface.log`
- Service logs: `power_snitch.service.log`
- Service error logs: `power_snitch.service.error.log`

Log rotation settings:
- Maximum file size: 10MB
- Backup files kept: 5
- Naming format: `filename.log.1`, `filename.log.2`, etc.

Viewing logs:
```bash
# View main application log
tail -f /var/log/power_snitch/power_snitch.log

# View web interface log
tail -f /var/log/power_snitch/web_interface.log

# View service logs
sudo journalctl -u power_snitch -f

# View all logs in real-time
tail -f /var/log/power_snitch/*.log
```

Cleaning old logs:
```bash
# Remove old log files (older than 30 days)
find /var/log/power_snitch -name "*.log.*" -mtime +30 -delete
```

### Restarting the Service
```bash
sudo systemctl restart power_snitch
```

## Firewall Configuration

The installation script automatically configures the firewall to allow access to the web interface port. By default, it:
1. Opens the configured port (default: 8080) in iptables
2. Makes the rules persistent across reboots
3. Enables the firewall service

To manage firewall rules manually:
```bash
# View current rules
sudo iptables -L

# Save current rules
sudo netfilter-persistent save

# Restore rules
sudo netfilter-persistent reload
```

## Troubleshooting

1. **UPS Not Detected**
   - Verify UPS is connected: `lsusb`
   - Check NUT driver: `sudo nut-scanner -U`
   - Verify NUT configuration: `sudo upsc ups`
   - Check NUT service status: `sudo systemctl status nut-server`

2. **Web Interface Not Accessible**
   - Check service status: `sudo systemctl status power_snitch`
   - Verify port is open: `sudo netstat -tulpn | grep <your-port>`
   - Check firewall settings: `sudo iptables -L`
   - Verify config file permissions: `ls -l /opt/power_snitch/config.yaml`

3. **Notifications Not Working**
   - Check configuration in `config.yaml`
   - Verify enabled services list
   - Check service logs for errors
   - Test webhook URL manually with curl
   - Verify email/SMS credentials

## Security Considerations

1. Change default web interface password immediately
2. Use strong passwords for all services
3. Store sensitive information securely in `config.yaml`
4. Consider using a reverse proxy with HTTPS for web interface
5. Restrict access to configuration files (600 permissions)
6. Regular monitoring of log files
7. Keep system and Python packages updated
8. Use firewall rules to restrict access to trusted IPs

## Uninstallation

To remove Power Snitch:

```bash
sudo systemctl stop power_snitch
sudo systemctl disable power_snitch
sudo rm /etc/systemd/system/power_snitch.service
sudo rm -rf /opt/power_snitch
sudo rm -rf /var/log/power_snitch

# Remove firewall rules
sudo iptables -D INPUT -p tcp --dport <your-port> -j ACCEPT
sudo netfilter-persistent save
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here] 