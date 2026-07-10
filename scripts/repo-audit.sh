#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0

check_tracked() {
  local pattern="$1"
  local label="$2"
  local matches
  matches="$(git ls-files | grep -E "$pattern" || true)"
  if [[ -n "$matches" ]]; then
    echo "ERROR: tracked $label:"
    echo "$matches"
    fail=1
  fi
}

check_tracked '(^|/)(venv|__pycache__|media|status|logs|backups)(/|$)' 'runtime/cache paths'
check_tracked '\.(pyc|pyo|log|tmp|bak)$' 'generated files'
check_tracked '(^|/)church-display-current.*\.tar\.gz$' 'audit archives'

if [[ -n "$(git status --porcelain)" ]]; then
  echo "WARNING: working tree is not clean:"
  git status --short
fi

python3 -m py_compile hub/app.py hub/routes/*.py hub/services/*.py
python3 -m py_compile display/app/*.py display/agent/*.py display/agent/jobs/*.py
python3 -m py_compile release/*.py

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi

echo "Repository audit passed."
