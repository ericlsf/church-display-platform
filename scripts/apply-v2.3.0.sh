#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chmod +x "$ROOT"/scripts/*.sh "$ROOT"/display/scripts/*.sh "$ROOT"/release/*.py 2>/dev/null || true
cd "$ROOT/hub"
source venv/bin/activate
python -m py_compile app.py routes/*.py services/*.py
PYTHONPATH=. python -m unittest discover -s tests -v
cd "$ROOT/display"
source venv/bin/activate
python -m py_compile app/*.py agent/*.py agent/jobs/*.py
printf '\nApplied v2.3.0 reliability foundation.\n'
