#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0

check_forbidden() {
  local pattern="$1"
  local label="$2"
  if git ls-files 2>/dev/null | grep -E "$pattern" >/dev/null; then
    echo "ERROR: tracked $label detected:" >&2
    git ls-files | grep -E "$pattern" >&2 || true
    fail=1
  fi
}

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  check_forbidden '(^|/)(venv|\.venv|__pycache__)(/|$)' 'environment/cache files'
  check_forbidden '(^|/)(media|logs|status|backups|previews)(/|$)' 'runtime files'
  check_forbidden '\.(pyc|pyo|log|tmp|db|sqlite|sqlite3)$' 'generated files'
  check_forbidden '(^|/)release/dist(/|$)' 'release build output'
fi

for required in \
  hub/app.py \
  display/agent/agent.py \
  display/scripts/sync_media.sh \
  release/build_release.py \
  release/verify.py \
  scripts/run-tests.sh; do
  if [ ! -f "$required" ]; then
    echo "ERROR: required file missing: $required" >&2
    fail=1
  fi
done

python3 -m py_compile release/*.py

if [ "$fail" -ne 0 ]; then
  exit 1
fi

echo "Repository audit passed."
