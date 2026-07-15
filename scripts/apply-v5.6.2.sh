#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.6.2.py

source hub/venv/bin/activate

python -m py_compile \
  display/agent/jobs/update.py \
  display/agent/install_version.py \
  display/agent/version.py \
  hub/services/deployment_verification.py \
  hub/services/version_compare.py

PYTHONPATH=hub:display python -m unittest \
  tests.test_version_compare \
  tests.test_deployment_verification_v562 \
  tests.test_authoritative_version \
  -v

PYTHONPATH=hub:display python - <<'PY'
from pathlib import Path

path = Path("display/agent/jobs/update.py")
text = path.read_text(encoding="utf-8")

dependency = text.index("_install_dependencies(report)")
record = text.index("record_installed_release(")
restart = text.index("_restart_and_verify(report)")

assert dependency < record < restart

print("Deployment handler integration order: PASS")
PY

echo
echo "v5.6.2 authoritative version integration applied."
echo "Run the production gate before deploying."
