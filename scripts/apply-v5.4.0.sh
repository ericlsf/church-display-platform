#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.4.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/display_upgrades.py \
  hub/services/display_upgrades.py \
  hub/services/display_details.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(
    loader=FileSystemLoader(str(root))
)
env.parse(
    (root / "display_details.html").read_text(
        encoding="utf-8"
    )
)
print("Display Details upgrade panel: PASS")
PY

echo
echo "v5.4.0 Safe One-Click Upgrades applied."
echo "Run the production gate before committing."
