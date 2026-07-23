#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v8.1.0.py
source hub/venv/bin/activate
python -m py_compile scripts/apply-v8.1.0.py

PYTHONPATH=hub python -m unittest tests.test_layout_v810 -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
base=Path("hub/templates/base.html").read_text(encoding="utf-8")
assert base.count("/static/layout-v8.1.js")==1
Environment(loader=FileSystemLoader("hub/templates")).parse(base)
css=Path("hub/static/style.css").read_text(encoding="utf-8")
assert "v8.1.0 layout refinement" in css
assert "--v8-sidebar-width:252px" in css.replace(" ","")
assert "--v8-breadcrumb-height:34px" in css.replace(" ","")
assert "top:var(--v8-topbar-height)!important" in css.replace(" ","")
print("v8.1.0 layout integration: PASS")
PY

echo
echo "v8.1.0 layout refinement applied."
echo "Run the production gate before committing."
