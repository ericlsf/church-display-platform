#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/hub"
source venv/bin/activate
PYTHONPATH=. python -m unittest discover -s tests -v
python -m py_compile app.py routes/*.py services/*.py
cd "$ROOT/display"
source venv/bin/activate
python -m py_compile app/*.py agent/*.py agent/jobs/*.py
