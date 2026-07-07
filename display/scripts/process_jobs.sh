#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"
DISPLAY_ID="${DISPLAY_ID:-$(hostname)}"

STATUS_DIR="$BASE_DIR/status"
mkdir -p "$STATUS_DIR"

JOB_FILE="$STATUS_DIR/current-job.json"

post_status() {
  local job_id="$1"
  local status="$2"
  local progress="$3"
  local message="$4"

  python3 - "$HUB_URL" "$job_id" "$status" "$progress" "$message" <<'PY'
import json
import sys
from urllib import request

hub_url, job_id, status, progress, message = sys.argv[1:6]

payload = {
    "status": status,
    "progress": progress,
    "message": message,
}

body = json.dumps(payload).encode("utf-8")
req = request.Request(
    f"{hub_url.rstrip()}/api/v1/jobs/{job_id}/status",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with request.urlopen(req, timeout=10) as resp:
    resp.read()
PY
}

fail_job() {
  local message="$1"
  post_status "$JOB_ID" "failed" "100" "$message"
  exit 1
}

get_next_job() {
  python3 - "$HUB_URL" "$DISPLAY_ID" "$JOB_FILE" <<'PY'
import json
import sys
from pathlib import Path
from urllib import parse, request

hub_url, display_id, job_file = sys.argv[1:4]
url = f"{hub_url.rstrip()}/api/v1/jobs/next?display_id={parse.quote(display_id)}"

try:
    with request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    data = {"ok": False, "error": str(e)}

Path(job_file).parent.mkdir(parents=True, exist_ok=True)
Path(job_file).write_text(json.dumps(data))
PY
}

json_field() {
  local field="$1"
  local default="$2"

  python3 - "$JOB_FILE" "$field" "$default" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
default = sys.argv[3]

try:
    data = json.load(open(sys.argv[1]))
    value = data.get("job", {})

    for part in path:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value in [None, ""]:
        value = default

    print(value)
except Exception:
    print(default)
PY
}

get_next_job

HAS_JOB="$(python3 - "$JOB_FILE" <<'PY'
import json
import sys

try:
    data = json.load(open(sys.argv[1]))
    print("yes" if data.get("job") else "no")
except Exception:
    print("no")
PY
)"

if [ "$HAS_JOB" != "yes" ]; then
  exit 0
fi

JOB_ID="$(json_field id "")"
JOB_TYPE="$(json_field type "")"
REMOTE="$(json_field payload.remote gdrive)"
FOLDER="$(json_field payload.folder Weekly)"

if [ -z "$JOB_ID" ] || [ -z "$JOB_TYPE" ]; then
  exit 1
fi

post_status "$JOB_ID" "running" "10" "Started $JOB_TYPE"

case "$JOB_TYPE" in
  sync_now)
    post_status "$JOB_ID" "running" "25" "Starting sync"

    if "$BASE_DIR/scripts/sync_media.sh"; then
      post_status "$JOB_ID" "success" "100" "Sync completed"
    else
      fail_job "Sync failed"
    fi
    ;;

  set_sync_folder)
    post_status "$JOB_ID" "running" "25" "Saving sync folder"

    if ! python3 - "$BASE_DIR/config/config.json" "$REMOTE" "$FOLDER" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
remote = sys.argv[2] or "gdrive"
folder = sys.argv[3] or "Weekly"

try:
    cfg = json.loads(path.read_text())
except Exception:
    cfg = {}

cfg.setdefault("sync", {})
cfg["sync"]["remote"] = remote
cfg["sync"]["folder"] = folder

path.parent.mkdir(parents=True, exist_ok=True)

tmp = path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(cfg, indent=2))
tmp.replace(path)
PY
    then
      fail_job "Failed to save sync folder"
    fi

    post_status "$JOB_ID" "running" "50" "Folder set to $FOLDER; starting sync"

    if "$BASE_DIR/scripts/sync_media.sh"; then
      post_status "$JOB_ID" "success" "100" "Folder set and sync completed"
    else
      fail_job "Folder set but sync failed"
    fi
    ;;

  restart_display)
    post_status "$JOB_ID" "success" "100" "Restart requested"
    sudo systemctl restart church-display.service
    ;;

  reboot)
    post_status "$JOB_ID" "success" "100" "Reboot requested"
    sudo reboot
    ;;

  upload_preview)
    post_status "$JOB_ID" "running" "25" "Uploading preview"

    if [ ! -x "$BASE_DIR/scripts/upload_preview_to_hub.sh" ]; then
      fail_job "Preview script not found or not executable"
    fi

    if "$BASE_DIR/scripts/upload_preview_to_hub.sh"; then
      post_status "$JOB_ID" "success" "100" "Preview uploaded"
    else
      fail_job "Preview upload failed"
    fi
    ;;

  heartbeat)
    post_status "$JOB_ID" "running" "25" "Sending heartbeat"

    if "$BASE_DIR/scripts/heartbeat_to_hub.sh"; then
      post_status "$JOB_ID" "success" "100" "Heartbeat sent"
    else
      fail_job "Heartbeat failed"
    fi
    ;;

  *)
    fail_job "Unknown job type: $JOB_TYPE"
    ;;
esac


