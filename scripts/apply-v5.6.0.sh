#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.6.0.py

source hub/venv/bin/activate

python -m py_compile \
  display/agent/version.py \
  display/agent/install_version.py \
  hub/routes/deployment_verification.py \
  hub/services/deployment_verification.py \
  scripts/apply-v5.6.0.py

PYTHONPATH=hub:display python -m unittest \
  tests.test_deployment_verification \
  tests.test_authoritative_version \
  -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

path = Path("hub/templates/display_details.html")
text = path.read_text(encoding="utf-8")

assert "data-deployment-verification" in text

environment = Environment(
    loader=FileSystemLoader("hub/templates")
)
environment.parse(text)

print("Deployment verification template: PASS")
PY

echo
echo "v5.6.0 self-verifying upgrades applied."
echo "Run the production gate before committing."
