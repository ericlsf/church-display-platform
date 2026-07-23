#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.5.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/health_diagnostics.py \
  hub/services/health_diagnostics.py \
  hub/services/display_details.py

PYTHONPATH=hub python -m unittest \
  tests.test_health_diagnostics \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

path = Path("hub/templates/display_details.html")
text = path.read_text(encoding="utf-8")

assert 'id="health-diagnostics"' in text
assert text.index("<h2>Health Diagnostics</h2>") < text.index("<h2>Recent Jobs</h2>")

env = Environment(loader=FileSystemLoader("hub/templates"))
env.parse(text)
print("Health diagnostics template: PASS")
PY

echo
echo "v5.5.0 Health Diagnostics applied."
echo "Run the production gate before committing."
