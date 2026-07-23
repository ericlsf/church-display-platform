#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
sudo python3 scripts/apply-v2.6.0.py
chmod +x scripts/create-admin.py
cd hub
source venv/bin/activate
python -m py_compile app.py routes/*.py services/*.py
echo
echo "Security update applied."
echo "Create the first admin account:"
echo "  cd $ROOT"
echo "  ./scripts/create-admin.py admin --display-name 'Administrator'"
echo "Then restart: sudo systemctl restart church-display-hub.service"
