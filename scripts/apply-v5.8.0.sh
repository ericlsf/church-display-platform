#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.8.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/automatic_rollback.py \
  hub/services/automatic_rollback.py \
  scripts/apply-v5.8.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_automatic_rollback \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/display_details.html"
).read_text(encoding="utf-8")

assert "data-automatic-rollback" in text

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

print("Automatic rollback UI integration: PASS")
PY

echo
echo "v5.8.0 automatic verification rollback applied."
echo "Run the production gate before committing."
