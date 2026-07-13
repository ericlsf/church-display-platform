#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="/etc/church-display"
SERVICE_DIR="/etc/systemd/system"
SUDOERS_FILE="/etc/sudoers.d/church-display-agent"

HUB_URL="${CHURCH_DISPLAY_HUB_URL:-}"
DISPLAY_NAME="${CHURCH_DISPLAY_NAME:-$(hostname)}"
DISPLAY_ID="${CHURCH_DISPLAY_ID:-$(hostname)}"
AUTO_START="${CHURCH_DISPLAY_AUTO_START:-yes}"
NON_INTERACTIVE="no"

usage() {
  cat <<'EOF'
Usage:
  ./install.sh --hub-url URL [options]

Options:
  --hub-url URL
  --display-name NAME
  --display-id ID
  --no-player
  --non-interactive
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub-url)
      HUB_URL="${2:-}"
      shift 2
      ;;
    --display-name)
      DISPLAY_NAME="${2:-}"
      shift 2
      ;;
    --display-id)
      DISPLAY_ID="${2:-}"
      shift 2
      ;;
    --no-player)
      AUTO_START="no"
      shift
      ;;
    --non-interactive)
      NON_INTERACTIVE="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this installer as the desktop user, not with sudo." >&2
  exit 1
fi

INSTALL_USER="$USER"
INSTALL_UID="$(id -u)"
HUB_URL="${HUB_URL%/}"

if [[ -z "$HUB_URL" ]]; then
  if [[ "$NON_INTERACTIVE" == "yes" ]]; then
    echo "--hub-url is required." >&2
    exit 2
  fi
  read -rp "Hub URL: " HUB_URL
  HUB_URL="${HUB_URL%/}"
fi

if [[ -z "$DISPLAY_NAME" && "$NON_INTERACTIVE" != "yes" ]]; then
  read -rp "Display name [$(hostname)]: " DISPLAY_NAME
  DISPLAY_NAME="${DISPLAY_NAME:-$(hostname)}"
fi

VERSION="$(cat "$APP_DIR/VERSION" 2>/dev/null || echo unknown)"
VERSION="${VERSION#v}"

echo
echo "Installing Church Display"
echo "-------------------------"
echo "Hub:     $HUB_URL"
echo "ID:      $DISPLAY_ID"
echo "Name:    $DISPLAY_NAME"
echo "Path:    $APP_DIR"
echo

echo "Installing operating-system dependencies..."
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl \
  ffmpeg \
  grim \
  imagemagick \
  jq \
  libegl1 \
  libgl1 \
  libxkbcommon-x11-0 \
  libxcb-cursor0 \
  python3 \
  python3-pip \
  python3-venv \
  scrot

echo "Creating Python environment..."
cd "$APP_DIR"
rm -rf venv
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt

echo "Preparing local data directories..."
mkdir -p media status logs config/backups

if [[ -d scripts ]]; then
  find scripts -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +
fi

if [[ ! -f config/config.json ]]; then
  cat > config/config.json <<'JSON'
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

echo "Writing Hub connection settings..."
sudo install -d -m 0755 "$ENV_DIR"
sudo tee "$ENV_DIR/heartbeat.env" >/dev/null <<EOF
HUB_URL=$HUB_URL
DISPLAY_ID=$DISPLAY_ID
DISPLAY_NAME=$DISPLAY_NAME
DISPLAY_PORT=8080
DISPLAY_VERSION=$VERSION
EOF
sudo cp "$ENV_DIR/heartbeat.env" "$ENV_DIR/register.env"

echo "Installing services..."
sudo tee "$SERVICE_DIR/church-display-agent.service" >/dev/null <<EOF
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
EOF

sudo tee "$SERVICE_DIR/church-display.service" >/dev/null <<EOF
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
EOF

sudo tee "$SUDOERS_FILE" >/dev/null <<EOF
$INSTALL_USER ALL=(root) NOPASSWD: /usr/bin/systemctl start church-display.service, /usr/bin/systemctl stop church-display.service, /usr/bin/systemctl restart church-display.service, /usr/bin/systemctl restart church-display-agent.service, /usr/sbin/reboot, /usr/sbin/shutdown
EOF
sudo chmod 0440 "$SUDOERS_FILE"
sudo visudo -cf "$SUDOERS_FILE" >/dev/null

for unit in \
  church-display-jobs.timer \
  church-display-heartbeat.timer \
  church-display-preview.timer \
  church-display-sync.timer \
  church-display-register.timer
do
  sudo systemctl disable --now "$unit" 2>/dev/null || true
done

sudo systemctl daemon-reload
sudo systemctl enable church-display-agent.service

if [[ "$AUTO_START" == "yes" ]]; then
  sudo systemctl enable church-display.service
else
  sudo systemctl disable church-display.service 2>/dev/null || true
fi

echo "Checking Hub connectivity..."
curl -fsS --max-time 15 "$HUB_URL/setup" >/dev/null

echo "Registering with the Hub..."
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

echo "Starting services..."
sudo systemctl restart church-display-agent.service

if [[ "$AUTO_START" == "yes" ]]; then
  sudo systemctl restart church-display.service || true
fi

sleep 5

FAILURES=0

if systemctl is-active --quiet church-display-agent.service; then
  echo "PASS  Agent is running"
else
  echo "FAIL  Agent is not running"
  FAILURES=$((FAILURES + 1))
fi

if curl -fsS --max-time 10 \
  "$HUB_URL/api/v1/jobs/next?display_id=$DISPLAY_ID" >/dev/null; then
  echo "PASS  Hub job endpoint is reachable"
else
  echo "FAIL  Hub job endpoint is not reachable"
  FAILURES=$((FAILURES + 1))
fi

if [[ "$AUTO_START" == "yes" ]]; then
  if systemctl is-active --quiet church-display.service; then
    echo "PASS  Display player is running"
  else
    echo "WARN  Player is waiting for the graphical Wayland session"
  fi
fi

if [[ "$FAILURES" -gt 0 ]]; then
  echo
  echo "Installation completed with $FAILURES failed check(s)."
  echo "Run:"
  echo "  sudo journalctl -u church-display-agent.service -n 100 --no-pager"
  exit 1
fi

echo
echo "Installation complete."
echo "Approve this display at:"
echo "  $HUB_URL/setup"
echo
echo "Pending display:"
echo "  $DISPLAY_NAME ($DISPLAY_ID)"
