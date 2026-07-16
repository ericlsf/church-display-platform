#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.7.0.py
source hub/venv/bin/activate

python -m py_compile   display/agent/dispatcher.py   display/agent/jobs/rollback.py   hub/routes/deployment_timeline.py   hub/services/deployment_timeline.py

PYTHONPATH=hub:display python -m unittest   tests.test_deployment_timeline   tests.test_rollback_handler   -v

PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
text = Path("hub/templates/display_details.html").read_text(encoding="utf-8")
assert "data-deployment-timeline" in text
assert 'job_type == "rollback_update"' in Path("display/agent/dispatcher.py").read_text(encoding="utf-8")
Environment(loader=FileSystemLoader("hub/templates")).parse(text)
print("Rollback dispatch and timeline template: PASS")
PY

echo
echo "v5.7.0 applied."
echo "Run the production gate before committing."
