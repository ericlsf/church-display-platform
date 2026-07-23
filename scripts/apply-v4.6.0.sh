#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/apply-v4.6.0.py
source hub/venv/bin/activate
python -m py_compile hub/app.py hub/routes/operations_center.py hub/services/operations_center.py
PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
root=Path("hub/templates"); env=Environment(loader=FileSystemLoader(str(root)))
env.parse((root/"operations_center.html").read_text())
print("Operations Center template: PASS")
PY
echo
echo "v4.6.0 Operations Center applied."
echo "Open: http://church-display-hub.local:8090/operations-center"
