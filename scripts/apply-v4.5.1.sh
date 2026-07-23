#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.5.1.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/fleet_operations.py \
  hub/services/fleet_operations.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))

for name in ("base.html", "fleet_operations.html"):
    env.parse((root / name).read_text(encoding="utf-8"))
    print(f"{name}: PASS")
PY

echo
echo "v4.5.1 Fleet Operations installed successfully."
echo "Open: http://church-display-hub.local:8090/fleet-operations"
