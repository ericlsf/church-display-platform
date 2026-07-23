#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v7.0.1.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v7.0.1.py

PYTHONPATH=hub python -m unittest \
  tests.test_navigation_v701 \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

base = Path(
    "hub/templates/base.html"
).read_text(encoding="utf-8")

assert base.count(
    "/static/navigation-v7.1.js"
) == 1

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(base)

css = Path(
    "hub/static/style.css"
).read_text(encoding="utf-8")

assert (
    "v7.0.1 sidebar vertical layout fix"
    in css
)
assert (
    "flex-direction: column !important"
    in css
)
assert (
    "grid-template-columns: minmax(0, 1fr)"
    in css
)

print("v7.0.1 vertical sidebar layout: PASS")
PY

echo
echo "v7.0.1 sidebar vertical layout fix applied."
echo "Run the production gate before committing."
