#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$BASE_DIR/config/config.json"
MEDIA_DIR="$BASE_DIR/media"
STATUS_DIR="$BASE_DIR/status"
LOG_DIR="$BASE_DIR/logs"
STATUS_FILE="$STATUS_DIR/sync.json"
LOCK_FILE="/tmp/church-display-sync.lock"

mkdir -p "$MEDIA_DIR" "$STATUS_DIR" "$LOG_DIR"

write_status() {
  local state="$1"
  local error="${2:-}"
  local duration="${3:-}"
  local files_synced="${4:-}"

  python3 - "$STATUS_FILE" "$state" "$error" "$duration" "$files_synced" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
state = sys.argv[2]
error = sys.argv[3]
duration = sys.argv[4]
files_synced = sys.argv[5]

payload = {
    "state": state,
    "error": error,
    "duration_seconds": duration,
    "files_synced": files_synced,
    "last_update": datetime.now().isoformat(timespec="seconds"),
}

if state == "success":
    payload["last_success"] = payload["last_update"]

try:
    if path.exists():
        old = json.loads(path.read_text())
        if "last_success" in old and state != "success":
            payload["last_success"] = old["last_success"]
except Exception:
    pass

tmp = path.with_suffix(path.suffix + ".tmp")
tmp.write_text(json.dumps(payload, indent=2))
tmp.replace(path)
PY
}

read_config_value() {
  local key="$1"
  local default="$2"

  python3 - "$CONFIG_FILE" "$key" "$default" <<'PY'
import json
import sys

config_file, key, default = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    with open(config_file, "r") as f:
        cfg = json.load(f)
    value = cfg.get("sync", {}).get(key, default)
    print(value)
except Exception:
    print(default)
PY
}

(
  flock -n 9 || {
    write_status "busy" "Another sync is already running"
    exit 0
  }

  START="$(date +%s)"
  REMOTE="$(read_config_value remote gdrive)"
  FOLDER="$(read_config_value folder Weekly)"
  SOURCE="${REMOTE}:${FOLDER}"
  LOG_FILE="$LOG_DIR/sync.log"

  write_status "running" "" "" ""

  echo "[$(date --iso-8601=seconds)] Starting sync from $SOURCE" >> "$LOG_FILE"

  OUTPUT="$(rclone sync "$SOURCE" "$MEDIA_DIR"     --delete-excluded     --include "*.jpg"     --include "*.jpeg"     --include "*.png"     --include "*.webp"     --include "*.mp4"     --include "*.mov"     --include "*.mkv"     --exclude "*"     --stats-one-line     --stats 10s 2>&1)"

  RC=$?
  END="$(date +%s)"
  DURATION="$((END - START))"

  echo "$OUTPUT" >> "$LOG_FILE"

  FILE_COUNT="$(find "$MEDIA_DIR" -type f \(     -iname "*.jpg" -o     -iname "*.jpeg" -o     -iname "*.png" -o     -iname "*.webp" -o     -iname "*.mp4" -o     -iname "*.mov" -o     -iname "*.mkv"   \) | wc -l)"

  if [ "$RC" -eq 0 ]; then
    echo "[$(date --iso-8601=seconds)] Sync successful from $SOURCE in ${DURATION}s; files=$FILE_COUNT" >> "$LOG_FILE"
    write_status "success" "" "$DURATION" "$FILE_COUNT"
  else
    echo "[$(date --iso-8601=seconds)] Sync failed from $SOURCE rc=$RC" >> "$LOG_FILE"
    write_status "error" "$OUTPUT" "$DURATION" "$FILE_COUNT"
    exit "$RC"
  fi

) 9>"$LOCK_FILE"



