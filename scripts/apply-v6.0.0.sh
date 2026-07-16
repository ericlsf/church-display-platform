#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.0.0.py

source hub/venv/bin/activate

python -m py_compile scripts/apply-v6.0.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_display_details_v600 \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path("hub/templates/display_details.html").read_text(encoding="utf-8")

assert 'class="display-hero"' in text
assert 'class="display-summary-grid"' in text
assert 'class="health-list-v600"' in text
assert text.count('id="health-diagnostics"') == 1

Environment(loader=FileSystemLoader("hub/templates")).parse(text)

print("v6.0.0 display details template: PASS")
PY

echo
echo "v6.0.0 display details UX refresh applied."
echo "Run the production gate before committing."
