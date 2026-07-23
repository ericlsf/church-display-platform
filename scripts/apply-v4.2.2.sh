#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.2.2.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/provisioning.py \
  hub/services/provisioning.py \
  display/app/cursor.py \
  display/app/main.py

PYTHONPATH=hub:display python - <<'PY'
from pathlib import Path

main = Path("display/app/main.py").read_text(encoding="utf-8")

assert main.count("from app.cursor import hide_cursor") == 1
assert main.count("hide_cursor(app)") == 1

print("Cursor integration: PASS")
print("Python compilation: PASS")
PY

echo
echo "v4.2.2 applied successfully."
