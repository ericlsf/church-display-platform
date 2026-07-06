#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_NAME="${USER}"
SERVICE_FILE="/etc/systemd/system/church-display.service"

cd "$APP_DIR"

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt
else
  python -m pip install PySide6 requests pillow watchdog
fi

mkdir -p media status logs config/backups scripts

echo "Creating systemd service at $SERVICE_FILE"

sudo tee "$SERVICE_FILE" >/dev/null <<EOF
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

sudo systemctl daemon-reload

echo
echo "Display install complete."
echo
echo "Manual dev run:"
echo "cd $APP_DIR && source venv/bin/activate && QT_QPA_PLATFORM=xcb python -m app.main"
echo
echo "Enable service:"
echo "sudo systemctl enable church-display.service"
echo "sudo systemctl start church-display.service"


