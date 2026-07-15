#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x \
  scripts/validate-runtime-imports.py \
  scripts/smoke-test-hub.py \
  scripts/verify-backup-restore.py \
  scripts/build-production-release.py \
  scripts/production-gate.sh

source hub/venv/bin/activate

python -m py_compile \
  scripts/validate-runtime-imports.py \
  scripts/smoke-test-hub.py \
  scripts/verify-backup-restore.py \
  scripts/build-production-release.py

echo
echo "v4.13.0 stabilization tools installed."
echo "Run: ./scripts/production-gate.sh"
