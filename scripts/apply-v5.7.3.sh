#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.7.3.py

source hub/venv/bin/activate

python -m py_compile scripts/apply-v5.7.3.py

PYTHONPATH=hub python -m unittest \
  tests.test_live_deployment_status \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/display_details.html"
).read_text(encoding="utf-8")

assert "/static/live-deployment-status.js" in text

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

print("Live deployment refresh integration: PASS")
PY

echo
echo "v5.7.3 live deployment status applied."
echo "Run the production gate before committing."
