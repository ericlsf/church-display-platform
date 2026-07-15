#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.4.1.py

source hub/venv/bin/activate
python -m py_compile scripts/apply-v5.4.1.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

path = Path("hub/templates/display_details.html")
text = path.read_text(encoding="utf-8")

for heading in ("Live Device Health", "Software Upgrade", "Recent Jobs"):
    assert f"<h2>{heading}</h2>" in text, heading

assert text.index("<h2>Live Device Health</h2>") < text.index("<h2>Recent Jobs</h2>")
assert text.index("<h2>Software Upgrade</h2>") < text.index("<h2>Recent Jobs</h2>")

env = Environment(loader=FileSystemLoader("hub/templates"))
env.parse(text)
print("Display page order and template: PASS")
PY

echo
echo "v5.4.1 display page layout applied."
