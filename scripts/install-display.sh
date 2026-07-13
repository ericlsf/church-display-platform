#!/usr/bin/env bash
set -euo pipefail

# Church Display Platform - fast display installer
#
# Run as the desktop user, not as root:
#   ./scripts/install-display.sh --hub-url http://church-display-hub.local:8090
#
# Expected platform:
#   Raspberry Pi OS Desktop (64-bit)
#   user: lsfservice

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DISPLAY_DIR="$PROJECT_ROOT/display"
ENV_DIR="/etc/church-display"
SYSTEMD_DIR="/etc/systemd/system"
SUDOERS_FILE="/etc/sudoers.d/church-display-agent"

HUB_URL=""
DISPLAY_NAME="$(hostname)"
DISPLAY_ID="$(hostname)"
DISPLAY_VERSION=""
START_PLAYER="yes"
NON_INTERACTIVE="no"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/install-display.sh [options]

Options:
  --hub-url URL          Hub URL, for example http://192.168.1.50:8090
  --display-name NAME    Friendly pending-enrollment name
  --display-id ID        Stable display ID (default: hostname)
  --version VERSION      Reported application version (default: current Git tag)
  --no-player            Install agent but do not enable the display player
  --non-interactive      Fail instead of prompting for missing values
  -h, --help             Show this help

Example:
  ./scripts/install-display.sh \
    --hub-url http://church-display-hub.local:8090 \
    --display-name "Lobby Display"
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
    --version)
      DISPLAY_VERSION="${2:-}"
      shift 2
      ;;
    --no-player)
      START_PLAYER="no"
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
      echo "Unknown option: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this script as the desktop user, not with sudo."
  echo "The script uses sudo only where system changes are required."
  exit 1
fi

INSTALL_USER="${SUDO_USER:-$USER}"
INSTALL_UID="$(id -u "$INSTALL_USER")"
INSTALL_HOME="$(getent passwd "$INSTALL_USER" | cut -d: -f6)"

if [[ "$INSTALL_USER" != "lsfservice" ]]; then
  echo "Warning: expected user 'lsfservice'; installing for '$INSTALL_USER'."
fi

if [[ ! -d "$DISPLAY_DIR/app" || ! -d "$DISPLAY_DIR/agent" ]]; then
  echo "Display source was not found at:"
  echo "  $DISPLAY_DIR"
  echo "Clone or extract the complete repository first."
  exit 1
fi

if [[ -z "$HUB_URL" ]]; then
  if [[ "$NON_INTERACTIVE" == "yes" ]]; then
    echo "--hub-url is required in non-interactive mode."
    exit 2
  fi

  read -rp "Hub URL [http://church-display-hub.local:8090]: " HUB_URL
  HUB_URL="${HUB_URL:-http://church-display-hub.local:8090}"
fi

HUB_URL="${HUB_URL%/}"

if [[ -z "$DISPLAY_VERSION" ]]; then
  DISPLAY_VERSION="$(
    git -C "$PROJECT_ROOT" describe --tags --always 2>/dev/null \
      | sed 's/^v//' \
      || true
  )"
  DISPLAY_VERSION="${DISPLAY_VERSION:-4.0.0}"
fi

echo
echo "Church Display installation"
echo "---------------------------"
echo "Repository:   $PROJECT_ROOT"
echo "User:         $INSTALL_USER"
echo "Display ID:   $DISPLAY_ID"
echo "Display name: $DISPLAY_NAME"
echo "Hub:          $HUB_URL"
echo "Version:      $DISPLAY_VERSION"
echo

echo "Installing operating-system packages..."
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl \
  ffmpeg \
  git \
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
  rclone \
  scrot

echo "Creating Python environment..."
cd "$DISPLAY_DIR"

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

source venv/bin/activate
python -m pip install --upgrade pip wheel

if [[ -f requirements.txt ]]; then
  python -m pip install -r requirements.txt
else
  python -m pip install PySide6 watchdog
fi

echo "Preparing directories and permissions..."
mkdir -p \
  "$DISPLAY_DIR/media" \
  "$DISPLAY_DIR/status" \
  "$DISPLAY_DIR/logs" \
  "$DISPLAY_DIR/config/backups"

chmod +x "$DISPLAY_DIR"/scripts/*.sh 2>/dev/null || true
chmod +x "$DISPLAY_DIR/scripts/sync_media.sh"

if [[ ! -f "$DISPLAY_DIR/config/config.json" ]]; then
  cat > "$DISPLAY_DIR/config/config.json" <<'EOF'
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
      {"day": "Sunday", "time": "08:00"},
      {"day": "Sunday", "time": "09:30"},
      {"day": "Sunday", "time": "11:15"}
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

echo "Writing display environment..."
sudo install -d -m 0755 "$ENV_DIR"

sudo tee "$ENV_DIR/heartbeat.env" >/dev/null <<EOF
HUB_URL=$HUB_URL
DISPLAY_ID=$DISPLAY_ID
DISPLAY_NAME=$DISPLAY_NAME
DISPLAY_PORT=8080
DISPLAY_VERSION=$DISPLAY_VERSION
EOF

sudo cp "$ENV_DIR/heartbeat.env" "$ENV_DIR/register.env"

echo "Installing system services..."

sudo tee "$SYSTEMD_DIR/church-display-agent.service" >/dev/null <<EOF
[Unit]
Description=Church Display Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$DISPLAY_DIR
EnvironmentFile=-$ENV_DIR/heartbeat.env
Environment=XDG_RUNTIME_DIR=/run/user/$INSTALL_UID
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DISPLAY=:0
ExecStart=$DISPLAY_DIR/venv/bin/python -m agent.agent
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee "$SYSTEMD_DIR/church-display.service" >/dev/null <<EOF
[Unit]
Description=Church Display Player
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$DISPLAY_DIR
Environment=QT_QPA_PLATFORM=wayland
Environment=XDG_RUNTIME_DIR=/run/user/$INSTALL_UID
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DISPLAY=:0
ExecStartPre=/usr/bin/test -S /run/user/$INSTALL_UID/wayland-0
ExecStart=$DISPLAY_DIR/venv/bin/python -m app.main
Restart=always
RestartSec=3

[Install]
WantedBy=graphical.target
EOF

echo "Restricting agent sudo access to approved recovery commands..."
sudo tee "$SUDOERS_FILE" >/dev/null <<EOF
$INSTALL_USER ALL=(root) NOPASSWD: \
/usr/bin/systemctl start church-display.service, \
/usr/bin/systemctl stop church-display.service, \
/usr/bin/systemctl restart church-display.service, \
/usr/bin/systemctl restart church-display-agent.service, \
/usr/sbin/reboot, \
/usr/sbin/shutdown
EOF
sudo chmod 0440 "$SUDOERS_FILE"
sudo visudo -cf "$SUDOERS_FILE"

echo "Disabling obsolete timer-based workers..."
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

if [[ "$START_PLAYER" == "yes" ]]; then
  sudo systemctl enable church-display.service
fi

echo "Testing Hub connectivity..."
if ! curl -fsS --max-time 10 "$HUB_URL/setup" >/dev/null; then
  echo
  echo "ERROR: The Hub did not respond at $HUB_URL."
  echo "The files and services were installed, but enrollment cannot continue."
  echo "Verify DNS/IP, firewall rules, and that the Hub service is running."
  exit 1
fi

echo "Registering this display with the Hub..."
IP_ADDRESS="$(hostname -I | awk '{print $1}')"
DISPLAY_HOST="http://${IP_ADDRESS}:8080"

python3 - "$HUB_URL" "$DISPLAY_NAME" "$DISPLAY_ID" "$IP_ADDRESS" "$DISPLAY_HOST" "$DISPLAY_VERSION" <<'PY'
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

echo "Starting the agent..."
sudo systemctl restart church-display-agent.service

if [[ "$START_PLAYER" == "yes" ]]; then
  echo "Starting the display player..."
  sudo systemctl restart church-display.service || true
fi

sleep 4

echo
echo "Post-install checks"
echo "-------------------"

FAILURES=0

if systemctl is-active --quiet church-display-agent.service; then
  echo "PASS  Display agent is active"
else
  echo "FAIL  Display agent is not active"
  FAILURES=$((FAILURES + 1))
fi

if [[ "$START_PLAYER" == "yes" ]]; then
  if systemctl is-active --quiet church-display.service; then
    echo "PASS  Display player is active"
  else
    echo "WARN  Display player is not active yet"
    echo "      It may start after the graphical Wayland session is available."
  fi
fi

if curl -fsS --max-time 10 "$HUB_URL/setup" >/dev/null; then
  echo "PASS  Hub is reachable"
else
  echo "FAIL  Hub is not reachable"
  FAILURES=$((FAILURES + 1))
fi

if curl -fsS --max-time 10 \
  "$HUB_URL/api/v1/jobs/next?display_id=$DISPLAY_ID" >/dev/null; then
  echo "PASS  Agent job endpoint is reachable"
else
  echo "FAIL  Agent job endpoint is not reachable"
  FAILURES=$((FAILURES + 1))
fi

echo
if [[ "$FAILURES" -gt 0 ]]; then
  echo "Installation completed with $FAILURES failed check(s)."
  echo
  echo "Inspect the agent:"
  echo "  sudo journalctl -u church-display-agent.service -n 100 --no-pager"
  exit 1
fi

echo "Display installation complete."
echo
echo "Approve it in the Hub:"
echo "  $HUB_URL/setup"
echo
echo "Pending display:"
echo "  $DISPLAY_NAME ($DISPLAY_ID)"
echo
echo "After approval, assign its site/group/playlist in the Hub."
echo
echo "Useful checks:"
echo "  sudo systemctl status church-display-agent.service --no-pager"
echo "  sudo systemctl status church-display.service --no-pager"
echo "  sudo journalctl -u church-display-agent.service -f"
