#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.1.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/fleet_dashboard.py \
  hub/routes/command_center_home.py \
  hub/services/fleet_dashboard.py \
  scripts/apply-v6.1.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_fleet_dashboard \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/fleet_dashboard.html"
).read_text(encoding="utf-8")

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

home = Path(
    "hub/routes/command_center_home.py"
).read_text(encoding="utf-8")

assert 'url_for("fleet_dashboard.page")' in home

print("Fleet dashboard template and landing route: PASS")
PY

echo
echo "v6.1.0 fleet dashboard applied."
echo "Run the production gate before committing."
