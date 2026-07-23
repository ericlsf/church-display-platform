#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="/etc/church-display"
SERVICE_DIR="/etc/systemd/system"
SUDOERS_FILE="/etc/sudoers.d/church-display-agent"

HUB_URL="${CHURCH_DISPLAY_HUB_URL:-}"
DISPLAY_NAME="${CHURCH_DISPLAY_NAME:-}"
RAW_DISPLAY_ID="${CHURCH_DISPLAY_ID:-$(hostname)}"
AUTO_START="${CHURCH_DISPLAY_AUTO_START:-yes}"
NON_INTERACTIVE="no"

normalize_id() {
  printf '%s' "$1" |
    tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

DISPLAY_ID="$(normalize_id "$RAW_DISPLAY_ID")"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub-url) HUB_URL="${2:-}"; shift 2 ;;
    --display-name) DISPLAY_NAME="${2:-}"; shift 2 ;;
    --display-id)
      RAW_DISPLAY_ID="${2:-}"
      DISPLAY_ID="$(normalize_id "$RAW_DISPLAY_ID")"
      shift 2
      ;;
    --no-player) AUTO_START="no"; shift ;;
    --non-interactive) NON_INTERACTIVE="yes"; shift ;;
    -h|--help)
      echo "Usage: ./install.sh --hub-url URL --display-name NAME --display-id ID [--no-player]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run as the desktop user, not with sudo." >&2
  exit 1
fi

HUB_URL="${HUB_URL%/}"
DISPLAY_NAME="${DISPLAY_NAME:-$(hostname)}"
DISPLAY_ID="${DISPLAY_ID:-$(normalize_id "$(hostname)")}"

[[ -n "$HUB_URL" ]] || { echo "Hub URL is required." >&2; exit 2; }
[[ -n "$DISPLAY_ID" ]] || { echo "Display ID is required." >&2; exit 2; }

VERSION="$(cat "$APP_DIR/VERSION" 2>/dev/null || echo unknown)"
VERSION="${VERSION#v}"
INSTALL_USER="$USER"
INSTALL_UID="$(id -u)"

echo "Installing required packages..."
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl ffmpeg grim imagemagick jq \
  libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 \
  python3 python3-pip python3-venv scrot

echo "Creating Python environment..."
cd "$APP_DIR"
rm -rf venv
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt

echo "Preparing local folders..."
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

echo "Writing display identity..."
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

sudo systemctl daemon-reload
sudo systemctl enable church-display-agent.service

if [[ "$AUTO_START" == "yes" ]]; then
  sudo systemctl enable church-display.service
else
  sudo systemctl disable church-display.service 2>/dev/null || true
fi

echo "Checking the Hub..."
curl -fsS --max-time 15 "$HUB_URL/setup" >/dev/null

IP_ADDRESS="$(hostname -I | awk '{print $1}')"
DISPLAY_HOST="http://${IP_ADDRESS}:8080"

echo "Registering..."
python3 - "$HUB_URL" "$DISPLAY_NAME" "$DISPLAY_ID" "$(hostname)" "$IP_ADDRESS" "$DISPLAY_HOST" "$VERSION" <<'PY'
import json
import sys
from urllib import request

hub_url, name, display_id, hostname, ip, host, version = sys.argv[1:8]
payload = {
    "name": name,
    "hostname": hostname,
    "id": display_id,
    "display_id": display_id,
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
    result = json.loads(response.read().decode("utf-8"))
    returned_id = result.get("display_id")
    if returned_id and returned_id != display_id:
        raise RuntimeError(
            f"Hub returned display ID '{returned_id}', "
            f"but installer is configured for '{display_id}'"
        )
    print(json.dumps(result))
PY

echo "Starting services..."
sudo systemctl restart church-display-agent.service
if [[ "$AUTO_START" == "yes" ]]; then
  sudo systemctl restart church-display.service || true
fi

sleep 5

FAILURES=0

systemctl is-active --quiet church-display-agent.service \
  || { echo "FAIL: agent service"; FAILURES=$((FAILURES + 1)); }

curl -fsS --max-time 10 \
  "$HUB_URL/api/v1/jobs/next?display_id=$DISPLAY_ID" >/dev/null \
  || { echo "FAIL: job endpoint"; FAILURES=$((FAILURES + 1)); }

curl -fsS --max-time 10 \
  "$HUB_URL/discovery/status?display_id=$DISPLAY_ID" >/dev/null \
  || { echo "FAIL: enrollment status endpoint"; FAILURES=$((FAILURES + 1)); }

if [[ "$FAILURES" -gt 0 ]]; then
  echo "Installation finished with $FAILURES failed check(s)." >&2
  exit 1
fi

echo "Display runtime installed successfully."
