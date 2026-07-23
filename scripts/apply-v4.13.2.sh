#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/verify-backup-restore.py

source hub/venv/bin/activate

python -m py_compile \
  scripts/verify-backup-restore.py \
  scripts/verify_backup_restore.py

PYTHONPATH=hub:. python -m unittest \
  tests.test_backup_snapshot \
  -v

echo
echo "v4.13.2 live backup verification applied."
echo "Run: ./scripts/production-gate.sh"
