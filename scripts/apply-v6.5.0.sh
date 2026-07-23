#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.5.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/alert_acknowledgements.py \
  hub/routes/alert_center.py \
  hub/services/alert_acknowledgements.py \
  hub/services/alert_center_state.py \
  scripts/apply-v6.5.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_alert_acknowledgements \
  tests.test_alert_center_state \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

template = Path(
    "hub/templates/alert_center.html"
).read_text(encoding="utf-8")

assert "/alerts/acknowledge" in template
assert "/alerts/restore" in template
assert "data-alert-panel" in template

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(template)

route = Path(
    "hub/routes/alert_center.py"
).read_text(encoding="utf-8")

assert "build_alert_center_state" in route

print("Alert acknowledgement UI and route: PASS")
PY

echo
echo "v6.5.0 alert acknowledgement applied."
echo "Run the production gate before committing."
