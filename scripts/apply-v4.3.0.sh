#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.3.0.py

source hub/venv/bin/activate
python -m py_compile \
  hub/app.py \
  hub/routes/display_releases.py \
  hub/routes/deployments.py \
  hub/services/display_releases.py \
  display/agent/jobs/update.py

PYTHONPATH=hub python - <<'PY'
from services.display_releases import validate_target
print("Display release service import: PASS")
PY

echo
echo "v4.3.0 Hub-managed software deployment applied."
