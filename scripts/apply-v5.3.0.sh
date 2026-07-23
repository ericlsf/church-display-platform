#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/apply-v5.3.0.py
source hub/venv/bin/activate
python -m py_compile hub/app.py hub/routes/command_center.py hub/services/command_center.py
PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))
env.parse((root / "command_center.html").read_text(encoding="utf-8"))
print("Command Center template: PASS")
PY
echo
echo "v5.3.0 Command Center applied."
echo "Run the production gate before committing."
