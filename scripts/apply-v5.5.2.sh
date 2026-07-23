#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.5.2.py

MARKER="/* v5.5.2 update card */"
if ! grep -Fq "$MARKER" hub/static/style.css; then
  {
    echo
    echo "$MARKER"
    cat hub/static/style.css.append
  } >> hub/static/style.css
fi
rm -f hub/static/style.css.append

source hub/venv/bin/activate
python -m py_compile hub/services/telemetry_normalization.py scripts/apply-v5.5.2.py

PYTHONPATH=hub python -m unittest tests.test_telemetry_normalization_v552 -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
text = Path("hub/templates/display_details.html").read_text(encoding="utf-8")
assert "update-stat-card" in text
assert text.index("<span>Health</span>") < text.index("update-stat-card")
assert text.index("update-stat-card") < text.index("<span>Media Files</span>")
env = Environment(loader=FileSystemLoader("hub/templates"))
env.parse(text)
print("Update card placement and template: PASS")
PY

echo
echo "v5.5.2 applied."
echo "Restart the Hub, then run the production gate."
