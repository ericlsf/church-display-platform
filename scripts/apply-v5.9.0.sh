#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.9.0.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v5.9.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_content_overlay_editor \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/display_details.html"
).read_text(encoding="utf-8")

assert "data-content-overlay-editor" in text
assert "/static/content-overlay-editor.js" in text

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

print("Content and overlay editor template: PASS")
PY

echo
echo "v5.9.0 live content and overlay editor applied."
echo "Run the production gate before committing."
