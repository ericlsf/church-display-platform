#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.2.0.py

source hub/venv/bin/activate

python -m py_compile scripts/apply-v5.2.0.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))

for name in ("base.html", "display_details.html"):
    env.parse((root / name).read_text(encoding="utf-8"))
    print(f"{name}: PASS")
PY

echo
echo "v5.2.0 visual polish applied."
echo "Run the production gate before committing."
