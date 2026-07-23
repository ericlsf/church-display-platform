#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.10.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/notifications.py \
  hub/services/notifications.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))
env.parse((root / "notifications.html").read_text(encoding="utf-8"))
env.parse((root / "base.html").read_text(encoding="utf-8"))
print("Notification templates: PASS")
PY

echo
echo "v4.10.0 Notification Center applied."
echo "Open: http://church-display-hub.local:8090/notifications"
