Requirements and Prerequisites
==============================

Supported environment
---------------------

Power Snitch currently targets:

- Debian-family Linux distributions
- Raspberry Pi OS
- ``systemd`` as the init system
- Locally attached USB UPS hardware

Host requirements
-----------------

Minimum practical host capabilities:

- Python 3.12 or a compatible system Python supported by the installer
- ``apt`` package management
- Sufficient permission to install packages and create ``/opt/powersnitch``
- A reachable LAN path to the host if remote browser access is required

Required software dependencies
------------------------------

The installer currently prepares or expects:

- ``nut``
- ``python3``
- ``python3-venv``
- ``python3-pip``
- ``sqlite3``
- ``curl``
- ``nut-scanner`` when available through the package repository

UPS prerequisites
-----------------

Before Power Snitch can discover or monitor a UPS, local NUT must be able to return:

- ``upsc -l``
- ``upsc <ups-name>``

If those commands do not work, Power Snitch cannot monitor the device yet. The installer now attempts to validate and optionally configure NUT for a USB-only local deployment, but some UPS models still require manual tuning.

Network prerequisites
---------------------

Review the host firewall before testing remote access. Power Snitch listens on TCP port ``8000`` by default.

If a firewall is enabled, confirm that inbound traffic to port ``8000`` is allowed from the expected management network.

Notification prerequisites
--------------------------

Each notification path has its own external dependency:

- Email requires a reachable SMTP relay.
- Telegram requires a bot token and chat ID.
- Twilio requires an account SID, auth token, and sender number.
- Webhook delivery requires a reachable endpoint.

Data storage prerequisites
--------------------------

Power Snitch uses SQLite by default and can run without InfluxDB. If you want telemetry mirrored to InfluxDB, set these runtime variables after install:

- ``POWERSNITCH_INFLUX_URL``
- ``POWERSNITCH_INFLUX_ORG``
- ``POWERSNITCH_INFLUX_BUCKET``
- ``POWERSNITCH_INFLUX_TOKEN``

