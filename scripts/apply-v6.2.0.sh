#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v6.2.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/bulk_operations.py \
  hub/services/bulk_operations.py \
  scripts/apply-v6.2.0.py

PYTHONPATH=hub python -m unittest \
  tests.test_bulk_operations \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/bulk_operations.html"
).read_text(encoding="utf-8")

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

base = Path(
    "hub/templates/base.html"
).read_text(encoding="utf-8")

assert "/bulk-operations/" in base

print("Bulk operations template and navigation: PASS")
PY

echo
echo "v6.2.0 bulk operations applied."
echo "Run the production gate before committing."
