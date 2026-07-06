#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt
else
  python -m pip install PySide6 requests pillow watchdog
fi

mkdir -p media status logs config/backups scripts

echo "Display install complete."
echo "Run with:"
echo "cd ~/church-display-platform/display && source venv/bin/activate && QT_QPA_PLATFORM=xcb python -m app.main"


