#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.8.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/audit.py \
  hub/services/audit.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))
env.parse((root / "audit.html").read_text(encoding="utf-8"))
print("Audit template: PASS")
PY

echo
echo "v4.8.0 Audit History applied."
echo "Open: http://church-display-hub.local:8090/audit"
