#!/bin/bash

set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
  echo "Please run this installer with sudo."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$SCRIPT_DIR"

INSTALL_USER="${SUDO_USER:-$USER}"
INSTALL_GROUP="$(id -gn "${INSTALL_USER}")"
APP_DIR="/opt/powersnitch"
VENV_DIR="$APP_DIR/.venv"
DATA_DIR="$APP_DIR/data"
ENV_FILE="$APP_DIR/runtime.env"
SERVICE_FILE="/etc/systemd/system/powersnitch.service"
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

nut_is_compatible() {
  "$VENV_DIR/bin/python" -m powersnitch_app.nut_setup --check-compatible >/dev/null 2>&1
}

configure_nut_for_powersnitch() {
  mkdir -p "$NUT_BACKUP_DIR"
  echo "Configuring NUT in standalone mode for local USB UPS monitoring..."
  "$VENV_DIR/bin/python" -m powersnitch_app.nut_setup --apply --backup-dir "$NUT_BACKUP_DIR"
  sleep 2
}

print_nut_requirements() {
  cat <<'EOF'
Power Snitch requires local NUT to provide UPS status via:
  upsc -l
  upsc <ups-name>

Minimum compatible settings:
  /etc/nut/nut.conf  -> MODE=standalone
  /etc/nut/ups.conf  -> at least one UPS definition
  nut-driver         -> running or able to start drivers
  nut-server         -> running successfully
EOF
}

echo "Installing Power Snitch dependencies..."
sudo apt update
sudo apt install -y \
  nut \
  python3 \
  python3-venv \
  python3-pip \
  sqlite3 \
  curl
if apt-cache show nut-scanner >/dev/null 2>&1; then
  sudo apt install -y nut-scanner
fi

echo "Preparing application directories..."
sudo mkdir -p "$APP_DIR" "$DATA_DIR"
sudo chown -R "$INSTALL_USER":"$INSTALL_GROUP" "$APP_DIR"

echo "Copying application files into $APP_DIR..."
tar \
  --exclude=".git" \
  --exclude="__pycache__" \
  --exclude=".pytest_cache" \
  --exclude=".mypy_cache" \
  --exclude=".ruff_cache" \
  --exclude=".venv" \
  --exclude="*.pyc" \
  -C "$SOURCE_DIR" \
  -cf - . | tar -C "$APP_DIR" -xf -

sudo chown -R "$INSTALL_USER":"$INSTALL_GROUP" "$APP_DIR"

cd "$APP_DIR"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

SESSION_SECRET=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)

mkdir -p "$DATA_DIR"
cat > "$ENV_FILE" <<EOF
POWERSNITCH_DATA_DIR=$DATA_DIR
POWERSNITCH_SQLITE_PATH=$DATA_DIR/powersnitch.db
POWERSNITCH_INITIAL_PASSWORD_FILE=$DATA_DIR/initial_admin_password.txt
POWERSNITCH_BIND_HOST=0.0.0.0
POWERSNITCH_PORT=8000
POWERSNITCH_SESSION_SECRET=$SESSION_SECRET
POWERSNITCH_STARTUP_DISCOVERY=true
EOF

set -a
. "$ENV_FILE"
set +a

echo "Bootstrapping Power Snitch database and admin credentials..."
"$VENV_DIR/bin/python" -m powersnitch_app.bootstrap
sudo chown -R "$INSTALL_USER":"$INSTALL_GROUP" "$DATA_DIR"

echo "Detected supported USB UPS devices:"
"$VENV_DIR/bin/python" -m powersnitch_app.nut_setup || true

if nut_is_compatible; then
  echo "Existing NUT configuration looks compatible with Power Snitch."
else
  echo "NUT is installed but not yet compatible with Power Snitch."
  if prompt_yes_default "May the installer configure local NUT for Power Snitch USB UPS autodiscovery?"; then
    configure_nut_for_powersnitch
  else
    print_nut_requirements
  fi
fi

NUT_DISCOVERY_OUTPUT="$(upsc -l 2>/dev/null || true)"
if [ -n "$NUT_DISCOVERY_OUTPUT" ]; then
  echo "NUT discovery succeeded:"
  printf '  %s\n' $NUT_DISCOVERY_OUTPUT
else
  echo "Warning: NUT did not return any UPS identifiers via 'upsc -l'."
  echo "Power Snitch will run, but UPS discovery in the UI will not work until NUT is configured correctly."
fi

sudo cp systemd/powersnitch.service "$SERVICE_FILE"
sudo sed -i "s|__APP_DIR__|$APP_DIR|g" "$SERVICE_FILE"
sudo sed -i "s|__USER__|$INSTALL_USER|g" "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable powersnitch.service

echo
echo "Power Snitch is installed."
echo "Initial admin password is stored at:"
echo "  $DATA_DIR/initial_admin_password.txt"
echo
echo "Next steps:"
echo "  sudo systemctl start powersnitch"
echo "  cat $DATA_DIR/initial_admin_password.txt"
echo "  browse to http://<server-ip>:8000"
