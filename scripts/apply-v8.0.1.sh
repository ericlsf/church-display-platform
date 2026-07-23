#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v8.0.1.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v8.0.1.py

PYTHONPATH=hub python -m unittest \
  tests.test_breadcrumb_v801 \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

base = Path(
    "hub/templates/base.html"
).read_text(encoding="utf-8")

assert base.count(
    "/static/breadcrumb-v8.1.js"
) == 1

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(base)

css = Path(
    "hub/static/style.css"
).read_text(encoding="utf-8")

assert "v8.0.1 breadcrumb layout fix" in css
assert "--v8-breadcrumb-height: 36px" in css
assert "overflow: visible !important" in css

print("v8.0.1 breadcrumb layout: PASS")
PY

echo
echo "v8.0.1 breadcrumb layout fix applied."
echo "Run the production gate before committing."
