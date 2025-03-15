#!/bin/bash
# Prompt for SSH password securely
read -s -p "Enter SSH Password: " SSHPASS
echo ""

# Define remote system details
REMOTE_USER="rion"
REMOTE_HOST="192.168.60.90"
LOCAL_DIR="/Users/rion/z_code/power_snitch/app"
REMOTE_DIR="/home/rion/power_snitch"
REMOTE_UNINSTALL="/home/rion/power_snitch/app/install/uninstall.sh"
REMOTE_INSTALL="/home/rion/power_snitch/app/install/install.sh"

# Use sshpass to provide the password automatically
sshpass -p "$SSHPASS" rsync -avz --exclude-from='deploy.exclude' "$LOCAL_DIR" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"
sshpass -p "$SSHPASS" ssh "$REMOTE_USER@$REMOTE_HOST" "sudo bash -c $REMOTE_UNINSTALL && sudo bash -c $REMOTE_INSTALL"


# Clear password variable for security
unset SSHPASS