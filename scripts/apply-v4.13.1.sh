#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/smoke-test-hub.py

source hub/venv/bin/activate

python -m py_compile scripts/smoke-test-hub.py

PYTHONPATH=hub python -m unittest \
  tests.test_smoke_expectations \
  -v

echo
echo "v4.13.1 smoke-test expectations applied."
echo "Run: ./scripts/production-gate.sh"
