#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.9.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/groups_maintenance.py \
  hub/services/display_groups.py \
  hub/services/maintenance.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))
env.parse((root / "groups_maintenance.html").read_text(encoding="utf-8"))
print("Groups & Maintenance template: PASS")
PY

echo
echo "v4.9.0 Groups & Maintenance applied."
echo "Open: http://church-display-hub.local:8090/fleet-config"
