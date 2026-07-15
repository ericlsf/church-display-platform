#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/fleet_operations.py \
  hub/services/fleet_operations.py

PYTHONPATH=hub python -m unittest \
  tests.test_group_targets \
  tests.test_display_groups \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))
env.parse((root / "fleet_operations.html").read_text(encoding="utf-8"))
print("Fleet Operations template: PASS")
PY

echo
echo "v4.9.1 group actions and maintenance enforcement applied."
