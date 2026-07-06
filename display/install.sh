#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_NAME="${USER}"
SERVICE_DIR="/etc/systemd/system"
ENV_DIR="/etc/church-display"

DISPLAY_SERVICE="$SERVICE_DIR/church-display.service"
SYNC_SERVICE="$SERVICE_DIR/church-display-sync.service"
SYNC_TIMER="$SERVICE_DIR/church-display-sync.timer"
REGISTER_SERVICE="$SERVICE_DIR/church-display-register.service"
REGISTER_TIMER="$SERVICE_DIR/church-display-register.timer"
HEARTBEAT_SERVICE="$SERVICE_DIR/church-display-heartbeat.service"
HEARTBEAT_TIMER="$SERVICE_DIR/church-display-heartbeat.timer"
PREVIEW_SERVICE="$SERVICE_DIR/church-display-preview.service"
PREVIEW_TIMER="$SERVICE_DIR/church-display-preview.timer"

cd "$APP_DIR"

echo "Installing Church Display Agent from:"
echo "$APP_DIR"
echo

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt
else
  python -m pip install PySide6 requests pillow watchdog
fi

mkdir -p media status logs config/backups scripts

if [ ! -f config/config.json ]; then
  cat > config/config.json <<'EOF'
{
  "overlay": {
    "enabled": true,
    "text": "Welcome"
  },
  "clock": {
    "enabled": true
  },
  "timings": {
    "image_duration": 8
  },
  "countdown": {
    "enabled": true,
    "start_minutes": 20,
    "services": [
      {
        "day": "Sunday",
        "time": "08:00"
      },
      {
        "day": "Sunday",
        "time": "09:30"
      },
      {
        "day": "Sunday",
        "time": "11:15"
      }
    ]
  },
  "dynamic_countdowns": [],
  "scheduled_overlays": [],
  "sync": {
    "remote": "gdrive",
    "folder": "Weekly"
  }
}
EOF
fi

sudo mkdir -p "$ENV_DIR"

if [ ! -f "$ENV_DIR/register.env" ]; then
  read -rp "Hub URL, example http://192.168.1.50:8090: " HUB_URL
  HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"

  sudo tee "$ENV_DIR/register.env" >/dev/null <<EOF
HUB_URL=$HUB_URL
DISPLAY_PORT=8080
DISPLAY_VERSION=1.2.1
EOF
fi

if [ ! -f "$ENV_DIR/heartbeat.env" ]; then
  sudo cp "$ENV_DIR/register.env" "$ENV_DIR/heartbeat.env"
  echo "DISPLAY_ID=$(hostname)" | sudo tee -a "$ENV_DIR/heartbeat.env" >/dev/null
fi

sudo tee "$DISPLAY_SERVICE" >/dev/null <<EOF
[Unit]
Description=Church Display
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python -m app.main
Restart=always
RestartSec=2

Environment=QT_QPA_PLATFORM=wayland
Environment=XDG_RUNTIME_DIR=/run/user/1000

[Install]
WantedBy=default.target
EOF

sudo tee "$SYNC_SERVICE" >/dev/null <<EOF
[Unit]
Description=Church Display Media Sync
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/scripts/sync_media.sh
EOF

sudo tee "$SYNC_TIMER" >/dev/null <<'EOF'
[Unit]
Description=Run Church Display Media Sync every minute

[Timer]
OnBootSec=30
OnUnitActiveSec=60
AccuracySec=10
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo tee "$REGISTER_SERVICE" >/dev/null <<EOF
[Unit]
Description=Register Church Display with Hub
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=-$ENV_DIR/register.env
ExecStart=$APP_DIR/scripts/register_with_hub.sh
EOF

sudo tee "$REGISTER_TIMER" >/dev/null <<'EOF'
[Unit]
Description=Register Church Display with Hub periodically

[Timer]
OnBootSec=45
OnUnitActiveSec=60
AccuracySec=10
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo tee "$HEARTBEAT_SERVICE" >/dev/null <<EOF
[Unit]
Description=Send Church Display heartbeat to Hub
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=-$ENV_DIR/heartbeat.env
ExecStart=$APP_DIR/scripts/heartbeat_to_hub.sh
EOF

sudo tee "$HEARTBEAT_TIMER" >/dev/null <<'EOF'
[Unit]
Description=Send Church Display heartbeat every 30 seconds

[Timer]
OnBootSec=30
OnUnitActiveSec=30
AccuracySec=5
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo tee "$PREVIEW_SERVICE" >/dev/null <<EOF
[Unit]
Description=Upload Church Display preview image to Hub
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=-$ENV_DIR/heartbeat.env
ExecStart=$APP_DIR/scripts/upload_preview_to_hub.sh
EOF

sudo tee "$PREVIEW_TIMER" >/dev/null <<'EOF'
[Unit]
Description=Upload Church Display preview image every minute

[Timer]
OnBootSec=60
OnUnitActiveSec=60
AccuracySec=10
Persistent=true

[Install]
WantedBy=timers.target
EOF

chmod +x scripts/*.sh 2>/dev/null || true

sudo systemctl daemon-reload

echo
echo "Install complete."
echo
echo "Enable display service:"
echo "sudo systemctl enable --now church-display.service"
echo
echo "Enable background timers:"
echo "sudo systemctl enable --now church-display-sync.timer"
echo "sudo systemctl enable --now church-display-register.timer"
echo "sudo systemctl enable --now church-display-heartbeat.timer"
echo "sudo systemctl enable --now church-display-preview.timer"
echo
echo "Manual dev run:"
echo "cd $APP_DIR && source venv/bin/activate && QT_QPA_PLATFORM=xcb python -m app.main"


