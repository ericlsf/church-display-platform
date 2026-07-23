#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/find-deployment-handler.py

source hub/venv/bin/activate

python -m py_compile \
  hub/services/live_display_telemetry.py \
  hub/services/deployment_verification.py \
  scripts/find-deployment-handler.py

PYTHONPATH=hub:display python -m unittest \
  tests.test_deployment_verification \
  tests.test_authoritative_version \
  -v

echo
echo "v5.6.1 verification dependency repaired."
echo
echo "Deployment handler candidates:"
PYTHONPATH=hub:display python \
  scripts/find-deployment-handler.py || true

echo
echo "Do not deploy v5.6.0 to a display until the active"
echo "deployment handler records VERSION before restarting the agent."
