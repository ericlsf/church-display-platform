#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/apply-v9.1.0.py
source hub/venv/bin/activate
python -m py_compile hub/routes/fleet_command_center.py hub/services/fleet_command_center.py scripts/apply-v9.1.0.py
PYTHONPATH=hub python -m unittest tests.test_fleet_command_center -v
PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
t=Path("hub/templates/fleet_command_center.html").read_text(encoding="utf-8")
Environment(loader=FileSystemLoader("hub/templates")).parse(t)
b=Path("hub/templates/base.html").read_text(encoding="utf-8")
assert "/static/fleet-command-center.css" in b
assert "/static/fleet-command-center.js" in t
assert "data-job-drawer" in t
assert "data-status-ribbon" in t
print("v9.1.0 Fleet Command Center integration: PASS")
PY
echo
echo "v9.1.0 Fleet Command Center applied."
echo "Run the production gate before committing."
