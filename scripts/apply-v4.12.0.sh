#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.12.0.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/display_profiles.py \
  hub/services/display_profiles.py

PYTHONPATH=hub python -m unittest \
  tests.test_display_profiles \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
environment = Environment(
    loader=FileSystemLoader(str(root))
)

for template_name in (
    "base.html",
    "display_profiles.html",
):
    environment.parse(
        (root / template_name).read_text(
            encoding="utf-8"
        )
    )
    print(f"{template_name}: PASS")
PY

echo
echo "v4.12.0 Display Profiles installed successfully."
echo "Open: http://church-display-hub.local:8090/display-profiles"
