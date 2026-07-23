#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.7.0.py

chmod +x scripts/process-rollouts.py

source hub/venv/bin/activate
python -m py_compile \
  hub/app.py \
  hub/routes/rollouts.py \
  hub/services/rollouts.py \
  scripts/process-rollouts.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))
env.parse((root / "rollouts.html").read_text(encoding="utf-8"))
print("Scheduled Rollouts template: PASS")
PY

sudo cp \
  hub/systemd/church-display-rollouts.service \
  /etc/systemd/system/church-display-rollouts.service

sudo cp \
  hub/systemd/church-display-rollouts.timer \
  /etc/systemd/system/church-display-rollouts.timer

sudo systemctl daemon-reload
sudo systemctl enable --now church-display-rollouts.timer

echo
echo "v4.7.0 Scheduled Rollouts applied."
