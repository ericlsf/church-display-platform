#!/usr/bin/env bash
set -u

BASE_DIR="/home/lsfservice/church-display-platform/display"

HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"
DISPLAY_PORT="${DISPLAY_PORT:-8080}"
DISPLAY_VERSION="${DISPLAY_VERSION:-1.1.0}"
DISPLAY_ID="${DISPLAY_ID:-$(hostname)}"

HOSTNAME_VALUE="$(hostname)"
IP_VALUE="$(hostname -I | awk '{print $1}')"
DISPLAY_HOST="http://${IP_VALUE}:${DISPLAY_PORT}"

python3 - "$BASE_DIR" "$HUB_URL" "$DISPLAY_ID" "$DISPLAY_HOST" "$HOSTNAME_VALUE" "$IP_VALUE" "$DISPLAY_VERSION" <<'PY'
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib import request

base = Path(sys.argv[1])
hub_url = sys.argv[2].rstrip("/")
display_id = sys.argv[3]
display_host = sys.argv[4]
hostname = sys.argv[5]
ip = sys.argv[6]
version = sys.argv[7]

def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}

def run(args):
    try:
        return subprocess.check_output(args, text=True, timeout=2).strip()
    except Exception:
        return "Unknown"

def cpu_temp():
    try:
        raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return f"{int(raw) / 1000:.1f}°C"
    except Exception:
        return "Unknown"

def disk_usage():
    try:
        return subprocess.check_output(["df", "-h", "/"], text=True).splitlines()[1].split()[4]
    except Exception:
        return "Unknown"

def memory_usage():
    try:
        data = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            data[k] = int(v.strip().split()[0])
        used = data["MemTotal"] - data["MemAvailable"]
        return f"{int((used / data['MemTotal']) * 100)}%"
    except Exception:
        return "Unknown"

payload = {
    "id": display_id,
    "hostname": hostname,
    "ip": ip,
    "host": display_host,
    "version": version,
    "config_version": 1,
    "sent_at": datetime.now().isoformat(timespec="seconds"),
    "player": read_json(base / "status" / "player.json"),
    "media": read_json(base / "status" / "media.json"),
    "sync": read_json(base / "status" / "sync.json"),
    "system": {
        "cpu_temp": cpu_temp(),
        "memory": memory_usage(),
        "disk": disk_usage(),
        "uptime": run(["uptime", "-p"]),
    },
}

body = json.dumps(payload).encode("utf-8")
req = request.Request(
    hub_url + "/api/v1/heartbeat",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with request.urlopen(req, timeout=5) as response:
    response.read()
PY


