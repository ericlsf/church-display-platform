#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.6.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/alert_rules.py \
  hub/routes/alert_center.py \
  hub/services/alert_rules.py \
  hub/services/alert_policy.py \
  scripts/apply-v6.6.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_alert_rules \
  tests.test_alert_policy \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

template = Path(
    "hub/templates/alert_rules.html"
).read_text(encoding="utf-8")

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(template)

route = Path(
    "hub/routes/alert_center.py"
).read_text(encoding="utf-8")

assert "apply_alert_policy" in route

print("Alert Rules template and policy integration: PASS")
PY

echo
echo "v6.6.0 alert rules applied."
echo "Run the production gate before committing."
