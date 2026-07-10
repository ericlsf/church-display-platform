#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCK_FILE="/tmp/church-display-sync.lock"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/sync.log"

(
  flock -n 9 || exit 0
  echo "[$(date --iso-8601=seconds)] Starting Hub LAN content sync" >> "$LOG_FILE"

  if "$BASE_DIR/venv/bin/python" -m agent.content_sync >> "$LOG_FILE" 2>&1; then
    echo "[$(date --iso-8601=seconds)] Hub LAN content sync successful" >> "$LOG_FILE"
    exit 0
  fi

  echo "[$(date --iso-8601=seconds)] Hub LAN sync failed; trying legacy Drive fallback" >> "$LOG_FILE"

  CONFIG_FILE="$BASE_DIR/config/config.json"
  MEDIA_DIR="$BASE_DIR/media"
  REMOTE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("sync",{}).get("remote","gdrive"))' "$CONFIG_FILE" 2>/dev/null || echo gdrive)"
  FOLDER="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("sync",{}).get("folder","Weekly"))' "$CONFIG_FILE" 2>/dev/null || echo Weekly)"

  mkdir -p "$MEDIA_DIR"
  rclone sync "${REMOTE}:${FOLDER}" "$MEDIA_DIR"     --delete-excluded     --filter '+ *.jpg' --filter '+ *.jpeg' --filter '+ *.png' --filter '+ *.webp'     --filter '+ *.mp4' --filter '+ *.mov' --filter '+ *.mkv' --filter '- *'     >> "$LOG_FILE" 2>&1
) 9>"$LOCK_FILE"
