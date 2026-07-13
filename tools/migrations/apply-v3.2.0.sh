#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/apply-v3.2.0.py
chmod +x display/scripts/*.sh scripts/*.sh
cd hub
source venv/bin/activate
python -m py_compile app.py routes/*.py services/*.py
cd ../display
source venv/bin/activate
python -m py_compile agent/*.py agent/jobs/*.py
