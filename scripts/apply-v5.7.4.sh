#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.7.4.py

MARKER="/* v5.7.4 stable upgrade card */"

if ! grep -Fq "$MARKER" hub/static/style.css; then
  {
    echo
    echo "$MARKER"
    cat hub/static/style.css.append
  } >> hub/static/style.css
fi

rm -f hub/static/style.css.append

source hub/venv/bin/activate

python -m py_compile \
  scripts/apply-v5.7.4.py

PYTHONPATH=hub python -m unittest \
  tests.test_upgrade_card_controller \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

text = Path(
    "hub/templates/display_details.html"
).read_text(encoding="utf-8")

assert text.count(
    "/static/live-deployment-status.js"
) == 1

assert (
    "/static/deployment-verification.js"
    not in text
)

assert (
    "/static/deployment-timeline.js"
    not in text
)

Environment(
    loader=FileSystemLoader("hub/templates")
).parse(text)

print("Single deployment-status controller: PASS")
PY

echo
echo "v5.7.4 stable upgrade card applied."
echo "Run the production gate before committing."
