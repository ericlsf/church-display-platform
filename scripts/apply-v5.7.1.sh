#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.7.1.py

source hub/venv/bin/activate

python -m py_compile \
  display/agent/dispatcher.py \
  display/agent/jobs/rollback.py \
  hub/routes/deployment_timeline.py \
  hub/services/deployment_timeline.py \
  scripts/apply-v5.7.1.py

PYTHONPATH=hub:display python -m unittest \
  tests.test_deployment_timeline \
  tests.test_rollback_handler \
  -v

PYTHONPATH=hub:display python - <<'PY'
from pathlib import Path
import re

dispatcher = Path(
    "display/agent/dispatcher.py"
).read_text(encoding="utf-8")

assert re.search(
    r"from\s+agent\.jobs\s+import[^\n]*\brollback\b",
    dispatcher,
)

assert re.search(
    r"""job_type\s*==\s*["']rollback_update["']""",
    dispatcher,
)

assert "rollback.handle_rollback_update(job, report)" in dispatcher

print("Rollback dispatcher integration: PASS")
PY

echo
echo "v5.7.1 dispatcher integration fixed."
echo "Run the production gate before committing."
