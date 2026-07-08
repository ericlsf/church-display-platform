#!/usr/bin/env bash
set -u

HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"
DISPLAY_ID="${DISPLAY_ID:-$(hostname)}"
TMP_FILE="/tmp/church-display-preview.jpg"

capture_preview() {
  if command -v grim >/dev/null 2>&1; then grim "$TMP_FILE" && return 0; fi
  if command -v scrot >/dev/null 2>&1; then scrot "$TMP_FILE" && return 0; fi
  if command -v gnome-screenshot >/dev/null 2>&1; then gnome-screenshot -f "$TMP_FILE" && return 0; fi
  if command -v import >/dev/null 2>&1; then import -window root "$TMP_FILE" && return 0; fi
  echo "No screenshot tool found. Install one of: grim, scrot, gnome-screenshot, imagemagick."
  return 1
}

if capture_preview; then
  curl -sS -X POST "$HUB_URL/api/v1/preview" \
    -F "id=$DISPLAY_ID" \
    -F "preview=@$TMP_FILE" >/dev/null
fi
