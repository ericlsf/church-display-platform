#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source hub/venv/bin/activate
python -m py_compile hub/routes/command_center.py hub/services/command_center.py tests/test_command_center_v920.py
PYTHONPATH=hub python -m unittest tests.test_command_center tests.test_command_center_v920 -v
python - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
root=Path('.')
Environment(loader=FileSystemLoader('hub/templates')).parse((root/'hub/templates/command_center.html').read_text())
assert (root/'hub/static/command-center-v920.css').exists()
assert '/static/command-center-v920.css' in (root/'hub/templates/command_center.html').read_text()
print('v9.2.0 operational cockpit integration: PASS')
PY
echo "v9.2.0 applied. Run ./scripts/production-gate.sh before committing."
