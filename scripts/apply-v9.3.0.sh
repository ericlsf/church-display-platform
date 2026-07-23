#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="backups/v9.3.0-$STAMP"
mkdir -p "$BACKUP/hub/templates" "$BACKUP/hub/static"
[[ -f hub/templates/command_center.html ]] && cp hub/templates/command_center.html "$BACKUP/hub/templates/"
[[ -f hub/static/command-center-v920.css ]] && cp hub/static/command-center-v920.css "$BACKUP/hub/static/"
[[ -f hub/static/command-center-v930.css ]] && cp hub/static/command-center-v930.css "$BACKUP/hub/static/"
install -m 0644 payload/hub/templates/command_center.html hub/templates/command_center.html
install -m 0644 payload/hub/static/command-center-v930.css hub/static/command-center-v930.css
python3 - <<'PY'
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
p = Path('hub/templates/command_center.html')
text = p.read_text(encoding='utf-8')
Environment(loader=FileSystemLoader('hub/templates')).parse(text)
assert '/static/command-center-v930.css' in text
assert 'class="breadcrumbs"' not in text
assert 'command-action-button' in text
assert 'command-health-inline' in text
print('v9.3.0 template validation: PASS')
PY
PYTHONPATH=hub python -m unittest tests.test_command_center_v930 -v
echo
echo "v9.3.0 applied. Backup: $BACKUP"
echo "Restart the hub and run scripts/production-gate.sh."
