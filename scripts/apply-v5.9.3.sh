#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.9.3.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v5.9.3.py

PYTHONPATH=hub python -m unittest \
  tests.test_simplified_content_editor \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/display_details.html"
).read_text(encoding="utf-8")

assert "content-editor-simple" in text
assert "content-preview-card" not in text
assert "/static/content-overlay-editor.js" not in text

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

print("Simplified content editor template: PASS")
PY

echo
echo "v5.9.3 simplified content editor applied."
echo "Run the production gate before committing."
