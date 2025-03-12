# Power Snitch

A UPS monitoring and notification system that provides real-time status monitoring, battery health tracking, and configurable notifications through webhook, email, and SMS.

## Features

- Real-time UPS status monitoring
- Battery health tracking and history
- Configurable notifications:
  - Webhook notifications
  - Email notifications
  - SMS notifications (via Twilio)
- Web interface for monitoring and configuration
- Daily health notifications
- Battery health alerts

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/power_snitch.git
cd power_snitch
```

2. Run the installation script:
```bash
sudo ./install.sh
```

The installation script will:
- Create necessary directories
- Install Python dependencies
- Initialize the database
- Set up systemd service
- Configure logging

## Default Credentials

- Default password: `password`
- Default web interface port: `5000`

You will be prompted to change these during the initial setup process.

## Web Interface

After installation, access the web interface at:
```
http://your-server:5000
```

The first time you access the interface:
1. Log in with the default password
2. Complete the initial setup process
3. Configure your UPS and notification settings

## Configuration

The web interface allows you to configure:
- UPS settings (name, description, poll interval)
- Notification services (webhook, email, SMS)
- Web interface settings (port, password)

## Logs

Logs are stored in:
- Application logs: `/var/log/power_snitch/power_snitch.log`
- Web interface logs: `/var/log/power_snitch/web_app.log`
- Database initialization logs: `/var/log/power_snitch/init_db.log`

## Requirements

- Python 3.8 or higher
- Network UPS Tools (NUT)
- SQLite3
- Systemd (for service management)

## License

MIT License - see LICENSE file for details 