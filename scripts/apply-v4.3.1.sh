#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CSS_APPEND="hub/static/style.css.append"
if [[ -f "$CSS_APPEND" ]]; then
  MARKER="/* v4.3.1 display presentation settings */"
  if ! grep -qF "$MARKER" hub/static/style.css; then
    {
      echo
      echo "$MARKER"
      cat "$CSS_APPEND"
    } >> hub/static/style.css
  fi
  rm -f "$CSS_APPEND"
fi

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/displays.py \
  display/agent/dispatcher.py \
  display/agent/jobs/settings.py

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

root = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(root)))
env.parse((root / "displays.html").read_text(encoding="utf-8"))
print("Template validation: PASS")
PY

echo
echo "v4.3.1 display presentation settings applied."
