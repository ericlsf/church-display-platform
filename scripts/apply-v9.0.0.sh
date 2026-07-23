#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/apply-v9.0.0.py
source hub/venv/bin/activate
python -m py_compile scripts/apply-v9.0.0.py
PYTHONPATH=hub python -m unittest tests.test_application_shell_v900 -v
PYTHONPATH=hub python - <<'PY'
from pathlib import Path
from jinja2 import Environment,FileSystemLoader
base=Path('hub/templates/base.html').read_text(encoding='utf-8')
shell=Path('hub/templates/application_shell.html').read_text(encoding='utf-8')
assert base.count('{% include "application_shell.html" %}')==1
assert base.count('/static/application-shell.css')==1
assert base.count('/static/application-shell.js')==1
for old in ('navigation-v7.js','navigation-v7.1.js','navigation-v8.js','breadcrumb-v8.1.js','layout-v8.1.js'): assert old not in base
env=Environment(loader=FileSystemLoader('hub/templates'));env.parse(base);env.parse(shell)
print('v9.0.0 single application shell: PASS')
PY
echo
echo 'v9.0.0 single application shell applied.'
echo 'Run the production gate before committing.'
