#!/usr/bin/env bash
set -euo pipefail

HUB_URL="${CHURCH_DISPLAY_HUB_URL:-__HUB_URL__}"
INSTALL_ROOT="/opt/church-display"
APP_DIR="$INSTALL_ROOT/display"
ENV_DIR="/etc/church-display"
SYSTEMD_DIR="/etc/systemd/system"
SUDOERS_FILE="/etc/sudoers.d/church-display-agent"
PACKAGE_URL="$HUB_URL/install/display/package.tar.gz"
DISPLAY_NAME="${CHURCH_DISPLAY_NAME:-}"
AUTO_START="${CHURCH_DISPLAY_AUTO_START:-yes}"

say() {
  printf '\n\033[1;36m%s\033[0m\n' "$1"
}

ok() {
  printf '\033[1;32m✓\033[0m %s\n' "$1"
}

die() {
  printf '\033[1;31mERROR:\033[0m %s\n' "$1" >&2
  exit 1
}

if [[ "$(id -u)" -eq 0 ]]; then
  die "Run this command as the desktop user, not with sudo."
fi

INSTALL_USER="$USER"
INSTALL_UID="$(id -u)"
DISPLAY_ID="$(hostname)"

clear 2>/dev/null || true
printf '%s\n' \
  '======================================' \
  '        Church Display Setup          ' \
  '======================================'

echo
echo "Hub found:"
echo "  $HUB_URL"
echo

read -rp "Use this Hub? [Y/n]: " USE_HUB
USE_HUB="${USE_HUB:-Y}"
if [[ ! "$USE_HUB" =~ ^[Yy]$ ]]; then
  read -rp "Enter Hub URL: " HUB_URL
  HUB_URL="${HUB_URL%/}"
  PACKAGE_URL="$HUB_URL/install/display/package.tar.gz"
fi

if [[ -z "$DISPLAY_NAME" ]]; then
  read -rp "Display name [$DISPLAY_ID]: " DISPLAY_NAME
  DISPLAY_NAME="${DISPLAY_NAME:-$DISPLAY_ID}"
fi

read -rp "Start automatically when the Pi boots? [Y/n]: " START_ANSWER
START_ANSWER="${START_ANSWER:-Y}"
if [[ "$START_ANSWER" =~ ^[Nn]$ ]]; then
  AUTO_START="no"
fi

echo
echo "Installing as:"
echo "  User:    $INSTALL_USER"
echo "  ID:      $DISPLAY_ID"
echo "  Name:    $DISPLAY_NAME"
echo "  Hub:     $HUB_URL"
echo
read -rp "Continue? [Y/n]: " CONTINUE
CONTINUE="${CONTINUE:-Y}"
[[ "$CONTINUE" =~ ^[Yy]$ ]] || exit 0

say "Checking the Hub"
curl -fsS --max-time 15 "$PACKAGE_URL" \
  -o /tmp/church-display-package.tar.gz \
  || die "Could not download the display package from $HUB_URL"
ok "Hub and display package are reachable"

say "Installing Raspberry Pi dependencies"
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl ffmpeg grim imagemagick jq libegl1 libgl1 \
  libxkbcommon-x11-0 libxcb-cursor0 python3 python3-pip \
  python3-venv scrot
ok "System dependencies installed"

say "Installing the display software"
sudo mkdir -p "$INSTALL_ROOT"
sudo rm -rf "$APP_DIR"
sudo tar -xzf /tmp/church-display-package.tar.gz -C "$INSTALL_ROOT"
sudo chown -R "$INSTALL_USER:$INSTALL_USER" "$INSTALL_ROOT"

mkdir -p \
  "$APP_DIR/media" \
  "$APP_DIR/status" \
  "$APP_DIR/logs" \
  "$APP_DIR/config/backups"

chmod +x "$APP_DIR"/scripts/*.sh 2>/dev/null || true
chmod +x "$APP_DIR/scripts/sync_media.sh"
ok "Display-only application installed"

say "Creating the Python environment"
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
ok "Python environment ready"

if [[ ! -f "$APP_DIR/config/config.json" ]]; then
  cat > "$APP_DIR/config/config.json" <<'JSON'
{
  "overlay": {"enabled": true, "text": "Welcome"},
  "clock": {"enabled": true},
  "timings": {"image_duration": 8},
  "countdown": {
    "enabled": true,
    "start_minutes": 20,
    "services": [
      {"day": "Sunday", "time": "08:00"},
      {"day": "Sunday", "time": "09:30"},
      {"day": "Sunday", "time": "11:15"}
    ]
  },
  "dynamic_countdowns": [],
  "scheduled_overlays": [],
  "sync": {"remote": "hub", "folder": ""}
}
JSON
fi

VERSION="$(cat "$APP_DIR/VERSION" 2>/dev/null || echo unknown)"
VERSION="${VERSION#v}"

say "Configuring services"
sudo install -d -m 0755 "$ENV_DIR"

sudo tee "$ENV_DIR/heartbeat.env" >/dev/null <<ENV
HUB_URL=$HUB_URL
DISPLAY_ID=$DISPLAY_ID
DISPLAY_NAME=$DISPLAY_NAME
DISPLAY_PORT=8080
DISPLAY_VERSION=$VERSION
ENV
sudo cp "$ENV_DIR/heartbeat.env" "$ENV_DIR/register.env"

sudo tee "$SYSTEMD_DIR/church-display-agent.service" >/dev/null <<SERVICE
[Unit]
Description=Church Display Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=-$ENV_DIR/heartbeat.env
Environment=XDG_RUNTIME_DIR=/run/user/$INSTALL_UID
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DISPLAY=:0
ExecStart=$APP_DIR/venv/bin/python -m agent.agent
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

sudo tee "$SYSTEMD_DIR/church-display.service" >/dev/null <<SERVICE
[Unit]
Description=Church Display Player
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$APP_DIR
Environment=QT_QPA_PLATFORM=wayland
Environment=XDG_RUNTIME_DIR=/run/user/$INSTALL_UID
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DISPLAY=:0
ExecStartPre=/usr/bin/test -S /run/user/$INSTALL_UID/wayland-0
ExecStart=$APP_DIR/venv/bin/python -m app.main
Restart=always
RestartSec=3

[Install]
WantedBy=graphical.target
SERVICE

sudo tee "$SUDOERS_FILE" >/dev/null <<SUDOERS
$INSTALL_USER ALL=(root) NOPASSWD: /usr/bin/systemctl start church-display.service, /usr/bin/systemctl stop church-display.service, /usr/bin/systemctl restart church-display.service, /usr/bin/systemctl restart church-display-agent.service, /usr/sbin/reboot, /usr/sbin/shutdown
SUDOERS
sudo chmod 0440 "$SUDOERS_FILE"
sudo visudo -cf "$SUDOERS_FILE" >/dev/null

sudo systemctl daemon-reload
sudo systemctl enable church-display-agent.service

if [[ "$AUTO_START" == "yes" ]]; then
  sudo systemctl enable church-display.service
fi

ok "Services configured"

say "Registering with the Hub"
IP_ADDRESS="$(hostname -I | awk '{print $1}')"
DISPLAY_HOST="http://${IP_ADDRESS}:8080"

python3 - "$HUB_URL" "$DISPLAY_NAME" "$DISPLAY_ID" "$IP_ADDRESS" "$DISPLAY_HOST" "$VERSION" <<'PY'
import json
import sys
from urllib import request

hub_url, name, display_id, ip, host, version = sys.argv[1:7]
payload = {
    "name": name,
    "hostname": display_id,
    "id": display_id,
    "ip": ip,
    "host": host,
    "version": version,
}
body = json.dumps(payload).encode("utf-8")
req = request.Request(
    f"{hub_url.rstrip('/')}/discovery/register",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with request.urlopen(req, timeout=15) as response:
    response.read()
PY

sudo systemctl restart church-display-agent.service

if [[ "$AUTO_START" == "yes" ]]; then
  sudo systemctl restart church-display.service || true
fi

sleep 4

say "Verifying installation"
systemctl is-active --quiet church-display-agent.service \
  || die "The display agent did not start"
ok "Display agent is active"

curl -fsS --max-time 10 \
  "$HUB_URL/api/v1/jobs/next?display_id=$DISPLAY_ID" >/dev/null \
  || die "The agent cannot reach the Hub job endpoint"
ok "Hub communication is working"

if [[ "$AUTO_START" == "yes" ]] && systemctl is-active --quiet church-display.service; then
  ok "Display player is active"
elif [[ "$AUTO_START" == "yes" ]]; then
  echo "WARN: Display player will start when the graphical Wayland session is ready."
fi

rm -f /tmp/church-display-package.tar.gz

printf '\n%s\n' \
  '======================================' \
  '        Installation Complete         ' \
  '======================================'
echo
echo "Display:"
echo "  $DISPLAY_NAME"
echo
echo "Approve it here:"
echo "  $HUB_URL/setup"
echo
echo "After approval, assign its site, group, and published playlist."
echo
echo "You should not need SSH again for normal operation."
