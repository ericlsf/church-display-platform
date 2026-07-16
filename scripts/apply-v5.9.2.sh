#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.9.2.py

source hub/venv/bin/activate

python -m py_compile scripts/apply-v5.9.2.py

PYTHONPATH=hub python -m unittest \
  tests.test_display_settings_layout \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/display_details.html"
).read_text(encoding="utf-8")

assert 'class="display-settings-layout"' in text
assert 'class="display-settings-content-row"' in text
assert 'class="display-settings-secondary-row"' in text

content = text.index("<h2>Content & Overlay</h2>")
profile = text.index("<h2>Display Profile</h2>")
maintenance = text.index("<h2>Maintenance</h2>")

assert content < profile < maintenance

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

print("Display settings row structure: PASS")
PY

echo
echo "v5.9.2 display settings layout applied."
echo "Run the production gate before committing."
