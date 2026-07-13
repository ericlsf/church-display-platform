#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x \
  display/install.sh \
  hub/static/install-display-bootstrap.sh

source hub/venv/bin/activate

python -m py_compile \
  hub/routes/display_installer.py

bash -n display/install.sh
bash -n hub/static/install-display-bootstrap.sh

PYTHONPATH=hub python -m unittest \
  tests.test_installer_identity \
  -v

echo
echo "v4.4.0 installer polish applied."
echo "Restart the Hub and test /install/display/health."
