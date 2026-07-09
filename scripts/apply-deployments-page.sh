#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

python3 scripts/apply-deployments-page.py

cd hub
source venv/bin/activate
python -m py_compile app.py routes/*.py services/*.py

echo
echo "Deployments page installed."
echo "Restart the Hub process, then open /deployments."
