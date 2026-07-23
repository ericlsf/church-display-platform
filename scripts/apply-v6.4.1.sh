#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.4.1.py

source hub/venv/bin/activate

python -m py_compile scripts/apply-v6.4.1.py

PYTHONPATH=hub python -m unittest \
  tests.test_fleet_operations_form_layout \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

path = Path("hub/templates/fleet_operations.html")
text = path.read_text(encoding="utf-8")

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

css = Path("hub/static/style.css").read_text(encoding="utf-8")

assert "v6.4.1 fleet operations form layout" in css
assert "grid-template-columns: minmax(0, 1fr)" in css

print("Fleet Operations form layout: PASS")
PY

echo
echo "v6.4.1 Fleet Operations form layout applied."
echo "Run the production gate before committing."
