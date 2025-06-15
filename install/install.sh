#!/bin/bash

set -e

# Install system dependencies
sudo apt update && sudo apt install -y \
    nut \
    python3 \
    python3-pip \
    sqlite3 \
    iptables-persistent

# Install Python dependencies
pip3 install \
    fastapi \
    uvicorn \
    aiohttp \
    aiosmtplib \
    pyyaml \
    pydantic \
    aiosqlite \
    python-json-logger

# Create application directory
sudo mkdir -p /opt/powersnitch
sudo chown $USER:$USER /opt/powersnitch

# Copy example config if it doesn't exist
if [ ! -f /opt/powersnitch/config.yaml ]; then
  cp config.yaml /opt/powersnitch/
fi

# Create empty database if not exists
if [ ! -f /opt/powersnitch/logs.db ]; then
  sqlite3 /opt/powersnitch/logs.db "VACUUM;"
fi

# Copy service file
sudo cp systemd/powersnitch.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable powersnitch

echo "\n✅ Power Snitch installed. You can now run:"
echo "   sudo systemctl start powersnitch"
echo "   sudo journalctl -u powersnitch -f"