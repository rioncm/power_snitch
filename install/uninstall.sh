#!/bin/bash

set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
  echo "Please run this uninstaller with sudo."
  exit 1
fi

APP_DIR="/opt/powersnitch"
SERVICE_FILE="/etc/systemd/system/powersnitch.service"
DATA_DIR="$APP_DIR/data"
NUT_BACKUP_DIR="$DATA_DIR/nut-backups"

prompt_yes_default() {
  local prompt="$1"
  local reply=""
  read -r -p "$prompt [Y/n] " reply || true
  case "${reply,,}" in
    n|no)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

restore_latest_backup() {
  local target="$1"
  local base
  base="$(basename "$target")"
  local latest=""
  latest="$(find "$NUT_BACKUP_DIR" -maxdepth 1 -type f -name "${base}.*.bak" | sort | tail -n 1)"
  if [ -n "$latest" ]; then
    cp "$latest" "$target"
    echo "Restored $target from $latest"
  else
    echo "No backup found for $target"
  fi
}

echo "Stopping Power Snitch service if it exists..."
if systemctl list-unit-files | grep -q '^powersnitch\.service'; then
  systemctl stop powersnitch.service || true
  systemctl disable powersnitch.service || true
fi

echo "Removing Power Snitch systemd unit..."
rm -f "$SERVICE_FILE"
systemctl daemon-reload

if [ -d "$APP_DIR" ]; then
  echo "Removing deployed application directory..."
  rm -rf "$APP_DIR"
else
  echo "Application directory not present: $APP_DIR"
fi

if prompt_yes_default "Do you want to restore the most recent NUT config backups created by the installer?"; then
  if [ -d "$NUT_BACKUP_DIR" ]; then
    restore_latest_backup /etc/nut/nut.conf
    restore_latest_backup /etc/nut/ups.conf
    if systemctl list-unit-files | grep -q '^nut-driver\.service'; then
      systemctl restart nut-driver || true
    fi
    if systemctl list-unit-files | grep -q '^nut-server\.service'; then
      systemctl restart nut-server || true
    fi
  else
    echo "No Power Snitch NUT backup directory found."
  fi
fi

echo "Power Snitch uninstall complete."
