#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting Hub..."
cd "$ROOT_DIR/hub"
source venv/bin/activate
nohup python app.py > "$ROOT_DIR/hub/logs/dev-hub.log" 2>&1 &
deactivate

echo "Starting Display..."
cd "$ROOT_DIR/display"
source venv/bin/activate
nohup env QT_QPA_PLATFORM=xcb python -m app.main > "$ROOT_DIR/display/logs/dev-display.log" 2>&1 &
deactivate

echo "Started."
echo "Hub log:     $ROOT_DIR/hub/logs/dev-hub.log"
echo "Display log: $ROOT_DIR/display/logs/dev-display.log"


