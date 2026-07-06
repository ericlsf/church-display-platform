#!/usr/bin/env bash
set -e

echo "Stopping manually running Hub and Display apps..."

pkill -f "church-display-platform/hub/app.py" 2>/dev/null || true
pkill -f "python app.py" 2>/dev/null || true
pkill -f "python -m app.main" 2>/dev/null || true

echo "Done."

