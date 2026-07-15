#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.6.1.py

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/deployments.py \
  hub/services/deployment_guard.py

PYTHONPATH=hub python -m unittest \
  tests.test_deployment_guard \
  -v

echo
echo "v4.6.1 deployment deduplication applied."
