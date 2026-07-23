#!/usr/bin/env bash
set -euo pipefail
TOKEN=""
HOSTNAME=""
ORIGIN="http://localhost:8090"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --token) TOKEN="${2:-}"; shift 2;;
    --hostname) HOSTNAME="${2:-}"; shift 2;;
    --origin) ORIGIN="${2:-}"; shift 2;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done
[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
[[ -n "$TOKEN" && -n "$HOSTNAME" ]] || { echo "Usage: sudo $0 --token 'eyJ...' --hostname 'hub.example.org'" >&2; exit 2; }
[[ "$TOKEN" == eyJ* ]] || { echo "The tunnel token should begin with eyJ." >&2; exit 2; }
[[ "$HOSTNAME" =~ ^[A-Za-z0-9.-]+$ ]] || { echo "Invalid hostname." >&2; exit 2; }

if ! command -v cloudflared >/dev/null 2>&1; then
  install -d -m 0755 /usr/share/keyrings
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
  echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' > /etc/apt/sources.list.d/cloudflared.list
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y cloudflared
fi

if systemctl list-unit-files cloudflared.service >/dev/null 2>&1; then
  systemctl stop cloudflared.service || true
  cloudflared service uninstall >/dev/null 2>&1 || true
fi
cloudflared service install "$TOKEN"
systemctl enable --now cloudflared.service

install -d -m 0755 /etc/church-display
python3 - "$HOSTNAME" "$ORIGIN" <<'PY'
import json, sys
from pathlib import Path
path = Path('/etc/church-display/remote-access.json')
path.write_text(json.dumps({'provider':'cloudflare','hostname':sys.argv[1],'origin':sys.argv[2]}, indent=2)+'\n', encoding='utf-8')
path.chmod(0o644)
PY

echo "Remote access service installed."
echo "Public URL: https://$HOSTNAME"
echo "Origin expected in Cloudflare: $ORIGIN"
echo "Verify that a Cloudflare Access Allow policy protects this hostname before use."
systemctl --no-pager --full status cloudflared.service | sed -n '1,14p'
