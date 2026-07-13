#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/apply-v2.7.0.py
cd hub
source venv/bin/activate
python -m py_compile app.py routes/*.py services/*.py
cd "$ROOT"
if [[ -x scripts/run-tests.sh ]]; then ./scripts/run-tests.sh; fi
echo "v2.7.0 applied. Restart church-display-hub.service and open /operations and /groups."
