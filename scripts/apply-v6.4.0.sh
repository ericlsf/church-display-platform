#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.4.0.py
source hub/venv/bin/activate

python -m py_compile   hub/routes/alert_center.py   hub/services/alert_center.py   hub/services/fleet_truth.py   hub/services/fleet_operations.py   scripts/apply-v6.4.0.py

PYTHONPATH=hub python -m unittest   tests.test_alert_center   tests.test_fleet_truth   -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

template = Path("hub/templates/alert_center.html").read_text(encoding="utf-8")
Environment(loader=FileSystemLoader("hub/templates")).parse(template)

fleet = Path("hub/services/fleet_operations.py").read_text(encoding="utf-8")
assert "def _fleet_rows_base(" in fleet
assert "v6.4.0 authoritative fleet-row wrapper" in fleet

print("Alert Center and fleet telemetry wrapper: PASS")
PY

echo
echo "v6.4.0 alert center and media truth applied."
echo "Run the production gate before committing."
