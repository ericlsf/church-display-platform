#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MARKER="/* v5.9.1 overlay preview containment */"

if ! grep -Fq "$MARKER" hub/static/style.css; then
  {
    echo
    echo "$MARKER"
    cat hub/static/style.css.append
  } >> hub/static/style.css
fi

rm -f hub/static/style.css.append

source hub/venv/bin/activate

PYTHONPATH=hub python -m unittest \
  tests.test_overlay_preview_layout \
  -v

echo
echo "v5.9.1 overlay preview layout fix applied."
echo "Run the production gate before committing."
