#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.5.1.py

source hub/venv/bin/activate

python -m py_compile   hub/services/telemetry_normalization.py   hub/services/fleet_operations.py

PYTHONPATH=hub python -m unittest   tests.test_telemetry_normalization   -v

echo
echo "v5.5.1 live telemetry truth applied."
echo "Restart the Hub, then run the production gate."
