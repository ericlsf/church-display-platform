#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/apply-v3.0.0.py
chmod +x scripts/*.sh
chmod +x display/scripts/*.sh 2>/dev/null || true
cd hub
if [[ -f venv/bin/activate ]]; then
  source venv/bin/activate
  python -m py_compile app.py routes/*.py services/*.py
else
  python3 -m py_compile app.py routes/*.py services/*.py
fi
echo
echo "v3.0.0 applied successfully. Restart the Hub and open /sites."
