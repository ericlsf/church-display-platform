#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v8.0.0.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v8.0.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_operator_ui_v800 \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

base = Path(
    "hub/templates/base.html"
).read_text(encoding="utf-8")

partial = Path(
    "hub/templates/navigation_shell.html"
).read_text(encoding="utf-8")

assert base.count(
    '{% include "navigation_shell.html" %}'
) == 1

assert base.count(
    "/static/navigation-v8.js"
) == 1

assert "v8-sidebar-search" in partial
assert "data-v8-section" in partial
assert "Administrator" not in partial
assert ">Home<" not in partial

environment = Environment(
    loader=FileSystemLoader("hub/templates")
)

environment.parse(base)
environment.parse(partial)

css = Path(
    "hub/static/style.css"
).read_text(encoding="utf-8")

assert "v8.0.0 operator UI polish" in css
assert "--v8-sidebar-width: 232px" in css
assert ".v8-main-content" in css

print("v8.0.0 operator UI integration: PASS")
PY

echo
echo "v8.0.0 operator UI polish applied."
echo "Run the production gate before committing."
