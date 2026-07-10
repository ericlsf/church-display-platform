#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$BASE_DIR/config/config.json"
MEDIA_DIR="$BASE_DIR/media"
STATUS_DIR="$BASE_DIR/status"
LOG_DIR="$BASE_DIR/logs"
STATUS_FILE="$STATUS_DIR/sync.json"
CHANGES_FILE="$STATUS_DIR/sync-changes.txt"
LOCK_FILE="/tmp/church-display-sync.lock"

mkdir -p "$MEDIA_DIR" "$STATUS_DIR" "$LOG_DIR"

write_status() {
  local state="$1" error="${2:-}" duration="${3:-}" files_synced="${4:-}"
  python3 - "$STATUS_FILE" "$CHANGES_FILE" "$state" "$error" "$duration" "$files_synced" <<'PY'
import json, sys
from datetime import datetime
from pathlib import Path
status_path, changes_path = Path(sys.argv[1]), Path(sys.argv[2])
state, error, duration, files_synced = sys.argv[3:7]
changes = {"added": [], "changed": [], "removed": [], "unchanged": []}
try:
    for line in changes_path.read_text().splitlines():
        if not line.strip(): continue
        marker, name = line[0], line[2:] if len(line) > 2 else line[1:]
        {"+":"added", "*":"changed", "-":"removed", "=":"unchanged"}.get(marker, "unchanged")
        bucket = {"+":"added", "*":"changed", "-":"removed", "=":"unchanged"}.get(marker)
        if bucket: changes[bucket].append(name)
except Exception:
    pass
payload = {
    "state": state, "error": error, "duration_seconds": duration,
    "files_synced": files_synced, "last_update": datetime.now().isoformat(timespec="seconds"),
    "changes": changes,
    "change_counts": {key: len(value) for key, value in changes.items()},
}
if state == "success": payload["last_success"] = payload["last_update"]
try:
    old=json.loads(status_path.read_text())
    if "last_success" in old and state != "success": payload["last_success"] = old["last_success"]
except Exception: pass
tmp=status_path.with_suffix(status_path.suffix+".tmp")
tmp.write_text(json.dumps(payload, indent=2)); tmp.replace(status_path)
PY
}

read_config_value() {
  python3 - "$CONFIG_FILE" "$1" "$2" <<'PY'
import json,sys
try: print(json.load(open(sys.argv[1])).get("sync",{}).get(sys.argv[2],sys.argv[3]))
except Exception: print(sys.argv[3])
PY
}

(
  flock -n 9 || { write_status "busy" "Another sync is already running"; exit 0; }
  START="$(date +%s)"
  REMOTE="$(read_config_value remote gdrive)"
  FOLDER="$(read_config_value folder Weekly)"
  SOURCE="${REMOTE}:${FOLDER}"
  LOG_FILE="$LOG_DIR/sync.log"
  : > "$CHANGES_FILE"
  write_status "running" "" "" ""
  echo "[$(date --iso-8601=seconds)] Starting sync from $SOURCE" >> "$LOG_FILE"

  OUTPUT="$(rclone sync "$SOURCE" "$MEDIA_DIR" \
    --delete-excluded \
    --filter '+ *.jpg' --filter '+ *.jpeg' --filter '+ *.png' --filter '+ *.webp' \
    --filter '+ *.mp4' --filter '+ *.mov' --filter '+ *.mkv' --filter '- *' \
    --combined "$CHANGES_FILE" --stats-one-line --stats 10s 2>&1)"
  RC=$?; END="$(date +%s)"; DURATION="$((END-START))"
  echo "$OUTPUT" >> "$LOG_FILE"
  FILE_COUNT="$(find "$MEDIA_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.mp4' -o -iname '*.mov' -o -iname '*.mkv' \) | wc -l)"
  if [ "$RC" -eq 0 ]; then
    echo "[$(date --iso-8601=seconds)] Sync successful from $SOURCE in ${DURATION}s; files=$FILE_COUNT" >> "$LOG_FILE"
    write_status "success" "" "$DURATION" "$FILE_COUNT"
  else
    echo "[$(date --iso-8601=seconds)] Sync failed from $SOURCE rc=$RC" >> "$LOG_FILE"
    write_status "error" "$OUTPUT" "$DURATION" "$FILE_COUNT"
    exit "$RC"
  fi
) 9>"$LOCK_FILE"
