#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v7.0.0.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v7.0.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_navigation_v700 \
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
    "/static/navigation-v7.js"
) == 1

for section in (
    "Dashboard",
    "Fleet",
    "Media",
    "Operations",
    "Administration",
):
    assert section in partial

environment = Environment(
    loader=FileSystemLoader("hub/templates")
)

environment.parse(base)
environment.parse(partial)

css = Path(
    "hub/static/style.css"
).read_text(encoding="utf-8")

assert "v7.0.0 navigation redesign" in css
assert ".v7-sidebar" in css
assert ".v7-topbar" in css
assert ".v7-breadcrumbs" in css

print("v7.0.0 navigation template integration: PASS")
PY

echo
echo "v7.0.0 navigation redesign applied."
echo "Run the production gate before committing."
