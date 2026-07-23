#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Validating Church Display source..."
echo

echo "1. Compiling active Python source"
mapfile -d '' PY_FILES < <(
  find hub display release scripts tests \
    -type d \( \
      -name venv -o \
      -name __pycache__ -o \
      -path '*/tools/migrations' \
    \) -prune -o \
    -type f -name '*.py' -print0
)

if [[ "${#PY_FILES[@]}" -gt 0 ]]; then
  python -m py_compile "${PY_FILES[@]}"
fi

echo "   Python compile: PASS"

echo "2. Parsing Jinja templates"
PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

templates_dir = Path("hub/templates")
env = Environment(loader=FileSystemLoader(str(templates_dir)))

for path in sorted(templates_dir.rglob("*.html")):
    env.parse(path.read_text(encoding="utf-8"))

print("   Template parse: PASS")
PY

echo "3. Running automated tests"
PYTHONPATH=hub python -m unittest discover -s tests -v

if [[ -x scripts/repo-audit.sh ]]; then
  echo "4. Running repository audit"
  ./scripts/repo-audit.sh
fi

echo
echo "Source validation passed."
