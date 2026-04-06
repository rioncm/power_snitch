#!/bin/bash

set -euo pipefail

APP_DIR="/opt/powersnitch"
VENV_DIR="$APP_DIR/.venv"
DATA_DIR="$APP_DIR/data"
ENV_FILE="$APP_DIR/runtime.env"
SERVICE_FILE="/etc/systemd/system/powersnitch.service"

echo "Installing Power Snitch dependencies..."
sudo apt update
sudo apt install -y \
  nut \
  python3 \
  python3-venv \
  python3-pip \
  sqlite3 \
  curl

echo "Preparing application directories..."
sudo mkdir -p "$APP_DIR" "$DATA_DIR"
sudo chown -R "$USER":"$USER" "$APP_DIR"

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
POWERSNITCH_BIND_HOST=127.0.0.1
POWERSNITCH_PORT=8000
POWERSNITCH_SESSION_SECRET=$SESSION_SECRET
POWERSNITCH_STARTUP_DISCOVERY=true
EOF

sudo cp systemd/powersnitch.service "$SERVICE_FILE"
sudo sed -i "s|__APP_DIR__|$APP_DIR|g" "$SERVICE_FILE"
sudo sed -i "s|__USER__|$USER|g" "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable powersnitch.service

echo
echo "Power Snitch is installed."
echo "Initial admin password will be written on first start to:"
echo "  $DATA_DIR/initial_admin_password.txt"
echo
echo "Next steps:"
echo "  sudo systemctl start powersnitch"
echo "  cat $DATA_DIR/initial_admin_password.txt"
echo "  browse to http://127.0.0.1:8000"
