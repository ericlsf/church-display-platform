#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v9.0.1.py
source hub/venv/bin/activate

python -m py_compile   scripts/apply-v9.0.1.py   tests/test_layout_v810.py   tests/test_navigation_v700.py   tests/test_application_shell_v901.py

PYTHONPATH=hub python -m unittest   tests.test_layout_v810   tests.test_navigation_v700   tests.test_application_shell_v900   tests.test_application_shell_v901   -v

echo
echo "v9.0.1 shell stabilization applied."
echo "Run the production gate before committing."
