#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.2.1.py

python3 - <<'PY'
from pathlib import Path

app = Path("hub/app.py")
text = app.read_text(encoding="utf-8")

import_line = "from routes.provisioning import provisioning_bp"
if import_line not in text:
    lines = text.splitlines()
    indexes = [
        i for i, line in enumerate(lines)
        if line.startswith("from routes.")
    ]
    lines.insert(max(indexes, default=0) + 1, import_line)
    text = "\n".join(lines) + "\n"

register = "    app.register_blueprint(provisioning_bp)"
if register not in text:
    lines = text.splitlines()
    indexes = [
        i for i, line in enumerate(lines)
        if "app.register_blueprint(" in line
    ]
    if not indexes:
        raise SystemExit("Could not find blueprint registrations")
    lines.insert(max(indexes) + 1, register)
    text = "\n".join(lines) + "\n"

app.write_text(text, encoding="utf-8")
PY

chmod +x display/install.sh 2>/dev/null || true

source hub/venv/bin/activate
python -m py_compile \
  hub/app.py \
  hub/routes/provisioning.py \
  hub/services/provisioning.py \
  display/app/cursor.py \
  display/app/main.py

echo
echo "v4.2.1 provisioning polish applied."
