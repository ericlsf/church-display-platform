#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.4.2.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v6.4.2.py

PYTHONPATH=hub python -m unittest \
  tests.test_fleet_operations_control_groups \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

template = Path(
    "hub/templates/fleet_operations.html"
).read_text(encoding="utf-8")

assert (
    "/static/fleet-operations-layout.js"
    in template
)

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(template)

script = Path(
    "hub/static/fleet-operations-layout.js"
).read_text(encoding="utf-8")

for label in (
    "Version",
    "Mode",
    "Overlay enabled",
    "Overlay text",
    "Clock enabled",
    "Countdown enabled",
    "Countdown window",
    "Image duration",
):
    assert label in script

print("Fleet Operations grouped controls: PASS")
PY

echo
echo "v6.4.2 Fleet Operations control groups applied."
echo "Run the production gate before committing."
